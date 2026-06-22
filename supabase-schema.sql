-- ============================================================================
--  Fable Tour Discovery  —  Supabase / PostgreSQL schema
--  ----------------------------------------------------------------------------
--  Run this in the Supabase SQL Editor (or via the CLI) once, top to bottom.
--  It is idempotent: safe to run again; seed data loads only when empty.
--
--  What it creates
--    profiles        one row per registered visitor (links to Supabase Auth)
--    media           photos / videos shown on each page (home + days 1-7)
--    quiz_questions  the 100-question pool (correct answer kept server-side)
--    quiz_served     remembers which questions a user saw today (no repeats)
--    quiz_scores     every attempt; leaderboard view shows each player's best
--    helper RPCs     next_quiz_round() and grade_quiz() for a cheat-proof quiz
--    storage bucket  'media' for real photo/video files (optional)
--
--  IMPORTANT — passwords:
--    Supabase Auth stores passwords *hashed*, so the "show my old password"
--    behaviour from the demo is not possible (and not safe) on a real backend.
--    Use Supabase's built-in password-reset email instead. Nationality is kept
--    in the profiles table below and passed at sign-up via user metadata.
-- ============================================================================

create extension if not exists pgcrypto;

-- ============================================================================
-- 1. PROFILES
-- ============================================================================
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text unique not null,
  nationality text,
  is_admin    boolean not null default false,
  created_at  timestamptz not null default now()
);
alter table public.profiles enable row level security;

-- Is the current user an administrator?  (support@fabletour.com is admin)
create or replace function public.is_admin()
returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select is_admin from public.profiles where id = auth.uid()), false);
$$;

-- Auto-create a profile whenever someone signs up through Supabase Auth.
-- Pass nationality in the sign-up call as: options.data = { nationality: '...' }
create or replace function public.handle_new_user()
returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, nationality, is_admin)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'nationality',
    lower(new.email) = 'support@fabletour.com'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

drop policy if exists "profiles self read"   on public.profiles;
drop policy if exists "profiles admin read"  on public.profiles;
drop policy if exists "profiles self update" on public.profiles;
create policy "profiles self read"   on public.profiles for select using (id = auth.uid());
create policy "profiles admin read"  on public.profiles for select using (public.is_admin());
create policy "profiles self update" on public.profiles for update using (id = auth.uid());

-- ============================================================================
-- 2. MEDIA  (photos & videos per page)
--    page_key is 'home' or '1'..'7' (matching the seven day pages)
--    kind is how the front-end renders src:
--      image     -> <img src=...>            (Storage URL or data URL)
--      video     -> <video src=...>          (Storage URL or data URL)
--      videourl  -> <video src=...>          (external direct .mp4 link)
--      youtube   -> embed, src = 11-char video id
--      vimeo     -> embed, src = numeric id
-- ============================================================================
create table if not exists public.media (
  id         bigint generated always as identity primary key,
  page_key   text not null check (page_key in ('home','1','2','3','4','5','6','7')),
  kind       text not null check (kind in ('image','video','videourl','youtube','vimeo')),
  src        text not null,
  alt        text,
  sort_order int  not null default 0,
  created_at timestamptz not null default now()
);
alter table public.media enable row level security;
create index if not exists media_page_idx on public.media (page_key, sort_order, created_at);

drop policy if exists "media public read" on public.media;
drop policy if exists "media admin write" on public.media;
create policy "media public read" on public.media for select using (true);
create policy "media admin write" on public.media for all
  using (public.is_admin()) with check (public.is_admin());

-- ============================================================================
-- 3. QUIZ QUESTIONS  (the 100-question pool)
--    The correct answer is never exposed to the browser: clients receive only
--    (id, question, options) via column privileges + the quiz_pool view, and
--    answers are graded server-side by grade_quiz().
-- ============================================================================
create table if not exists public.quiz_questions (
  id            bigint generated always as identity primary key,
  question      text not null,
  options       jsonb not null,                       -- array of 4 strings
  correct_index int  not null check (correct_index between 0 and 3),
  active        boolean not null default true,
  created_at    timestamptz not null default now()
);
alter table public.quiz_questions enable row level security;

drop policy if exists "questions public read" on public.quiz_questions;
drop policy if exists "questions admin all"   on public.quiz_questions;
create policy "questions public read" on public.quiz_questions
  for select to anon, authenticated using (active);
create policy "questions admin all" on public.quiz_questions
  for all using (public.is_admin()) with check (public.is_admin());

-- Hide the answer column: revoke full select, grant only the safe columns.
revoke select on public.quiz_questions from anon, authenticated;
grant  select (id, question, options) on public.quiz_questions to anon, authenticated;

-- Convenience view with no answer column.
create or replace view public.quiz_pool with (security_invoker = on) as
  select id, question, options from public.quiz_questions where active;
grant select on public.quiz_pool to anon, authenticated;

-- ============================================================================
-- 4. QUIZ SERVED  (so the same question never repeats for a user the same day)
-- ============================================================================
create table if not exists public.quiz_served (
  user_id     uuid   not null references auth.users(id) on delete cascade,
  served_on   date   not null default current_date,
  question_id bigint not null references public.quiz_questions(id) on delete cascade,
  primary key (user_id, served_on, question_id)
);
alter table public.quiz_served enable row level security;

drop policy if exists "served self" on public.quiz_served;
create policy "served self" on public.quiz_served for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- ============================================================================
-- 5. QUIZ SCORES + LEADERBOARD  (player_name/nationality denormalised so the
--    public leaderboard never exposes email addresses)
-- ============================================================================
create table if not exists public.quiz_scores (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  player_name text not null,
  nationality text,
  score       int  not null check (score between 0 and 10),
  total       int  not null default 10,
  created_at  timestamptz not null default now()
);
alter table public.quiz_scores enable row level security;
create index if not exists scores_best_idx on public.quiz_scores (score desc, created_at);

drop policy if exists "scores public read" on public.quiz_scores;
drop policy if exists "scores self insert" on public.quiz_scores;
create policy "scores public read" on public.quiz_scores for select using (true);
create policy "scores self insert" on public.quiz_scores for insert
  with check (user_id = auth.uid());

-- Best score per player (the leaderboard).  Order client-side: ... order by score desc.
create or replace view public.leaderboard with (security_invoker = on) as
  select distinct on (user_id)
         user_id, player_name, nationality, score, total, created_at
  from public.quiz_scores
  order by user_id, score desc, created_at asc;
grant select on public.leaderboard to anon, authenticated;

-- ============================================================================
-- 6. RPCs  —  call these from the browser with supabase.rpc(...)
-- ============================================================================

-- Draw the next round of questions for the signed-in user.
-- Excludes anything already served today; if fewer than p_count remain,
-- today's history resets so play can continue.  Records what it serves.
create or replace function public.next_quiz_round(p_count int default 10)
returns table(id bigint, question text, options jsonb)
language plpgsql security definer set search_path = public as $$
declare
  uid   uuid := auth.uid();
  avail int;
begin
  if uid is null then
    raise exception 'You must be signed in to take the quiz.';
  end if;

  select count(*) into avail
  from public.quiz_questions q
  where q.active
    and not exists (
      select 1 from public.quiz_served s
      where s.user_id = uid and s.served_on = current_date and s.question_id = q.id
    );

  if avail < p_count then
    delete from public.quiz_served where user_id = uid and served_on = current_date;
  end if;

  return query
  with picked as (
    select q.id, q.question, q.options
    from public.quiz_questions q
    where q.active
      and not exists (
        select 1 from public.quiz_served s
        where s.user_id = uid and s.served_on = current_date and s.question_id = q.id
      )
    order by random()
    limit p_count
  ),
  remember as (
    insert into public.quiz_served (user_id, served_on, question_id)
    select uid, current_date, picked.id from picked
    on conflict do nothing
    returning question_id
  )
  select picked.id, picked.question, picked.options from picked;
end;
$$;
grant execute on function public.next_quiz_round(int) to authenticated;

-- Grade a finished round and record the score.
-- p_answers is a JSON array like:  [{"id": 12, "choice": 2}, {"id": 7, "choice": 0}, ...]
-- where "choice" is the index (0-3) into that question's original options array.
create or replace function public.grade_quiz(p_answers jsonb)
returns table(score int, total int)
language plpgsql security definer set search_path = public as $$
declare
  uid     uuid := auth.uid();
  v_score int  := 0;
  v_total int  := 0;
  v_name  text;
  v_nat   text;
  rec     jsonb;
begin
  if uid is null then
    raise exception 'You must be signed in to submit a score.';
  end if;

  for rec in select jsonb_array_elements(p_answers) loop
    v_total := v_total + 1;
    if exists (
      select 1 from public.quiz_questions q
      where q.id = (rec->>'id')::bigint
        and q.correct_index = (rec->>'choice')::int
    ) then
      v_score := v_score + 1;
    end if;
  end loop;

  select nationality, coalesce(nullif(initcap(replace(split_part(email,'@',1), '.', ' ')), ''), 'Scholar')
    into v_nat, v_name
  from public.profiles where id = uid;

  insert into public.quiz_scores (user_id, player_name, nationality, score, total)
  values (uid, v_name, v_nat, v_score, v_total);

  return query select v_score, v_total;
end;
$$;
grant execute on function public.grade_quiz(jsonb) to authenticated;

-- Admin-only view of sign-ups (email + nationality + when), for the dashboard.
create or replace view public.admin_signups with (security_invoker = on) as
  select email, nationality, created_at
  from public.profiles
  order by created_at desc;
grant select on public.admin_signups to authenticated;
-- (Only admins can read profiles, so non-admins see no rows through this view.)

-- ============================================================================
-- 7. OPTIONAL — email support@fabletour.com on every new sign-up
--    Requires pg_net + a deployed Edge Function that actually sends mail
--    (e.g. using Resend / Postmark / SendGrid). Uncomment and fill in.
-- ============================================================================
-- create extension if not exists pg_net;
--
-- create or replace function public.notify_new_signup()
-- returns trigger language plpgsql security definer set search_path = public as $$
-- begin
--   perform net.http_post(
--     url     := 'https://<YOUR-PROJECT-REF>.functions.supabase.co/notify-signup',
--     headers := jsonb_build_object(
--                  'Content-Type','application/json',
--                  'Authorization','Bearer <YOUR-FUNCTION-SECRET>'),
--     body    := jsonb_build_object(
--                  'to','support@fabletour.com',
--                  'subject','New Fable Tour Discovery sign-up',
--                  'email', new.email,
--                  'nationality', new.nationality)
--   );
--   return new;
-- end;
-- $$;
--
-- drop trigger if exists on_profile_created_notify on public.profiles;
-- create trigger on_profile_created_notify
--   after insert on public.profiles
--   for each row execute function public.notify_new_signup();

-- ============================================================================
-- 8. OPTIONAL — Storage bucket for real photo/video files
--    Upload files to this bucket from the dashboard, then store the public URL
--    in media.src with kind 'image' or 'video'. Better than data URLs for big files.
-- ============================================================================
insert into storage.buckets (id, name, public)
values ('media','media', true)
on conflict (id) do nothing;

drop policy if exists "media bucket public read"  on storage.objects;
drop policy if exists "media bucket admin insert"  on storage.objects;
drop policy if exists "media bucket admin update"  on storage.objects;
drop policy if exists "media bucket admin delete"  on storage.objects;
create policy "media bucket public read" on storage.objects
  for select using (bucket_id = 'media');
create policy "media bucket admin insert" on storage.objects
  for insert with check (bucket_id = 'media' and public.is_admin());
create policy "media bucket admin update" on storage.objects
  for update using (bucket_id = 'media' and public.is_admin());
create policy "media bucket admin delete" on storage.objects
  for delete using (bucket_id = 'media' and public.is_admin());

-- ============================================================================
-- 9. SEED — the 100 quiz questions (loads only if the table is empty)
-- ============================================================================
insert into public.quiz_questions (question, options, correct_index)
select v.question, v.options, v.correct_index
from (values
    ('The Code of Hammurabi is most associated with which ancient city?', '["Ur","Babylon","Nineveh","Hatra"]'::jsonb, 1),
    ('The Code of Hammurabi is famous as an early example of what?', '["A calendar","A written law code","A map","A poem"]'::jsonb, 1),
    ('Babylon’s reconstructed monumental gate is known as the?', '["Lion Gate","Ishtar Gate","Gate of Nabu","Marduk Gate"]'::jsonb, 1),
    ('Which Neo-Babylonian king is most associated with Babylon’s height?', '["Sargon","Nebuchadnezzar II","Ashurbanipal","Cyrus"]'::jsonb, 1),
    ('Babylon lay in the historical region known as?', '["Anatolia","Mesopotamia","Persia","Nubia"]'::jsonb, 1),
    ('The Ishtar Gate is famous for glazed brick of which dominant colour?', '["Green","Blue","Red","White"]'::jsonb, 1),
    ('The great ziggurat of Borsippa was dedicated to which god?', '["Marduk","Nabu","Enlil","Nanna"]'::jsonb, 1),
    ('Nabu was the Mesopotamian god of what?', '["War","Wisdom and writing","The sea","Harvest"]'::jsonb, 1),
    ('The Shrine of Prophet Job (Ayub) honours a figure symbolising what?', '["Wealth","Patience","Conquest","Speed"]'::jsonb, 1),
    ('Prophet Job is revered across which three faiths?', '["Only Islam","Islam, Christianity and Judaism","Only Christianity","Hinduism and Buddhism"]'::jsonb, 1),
    ('Babylon pioneered advances in mathematics and which sky-watching science?', '["Geology","Astronomy","Botany","Zoology"]'::jsonb, 1),
    ('Babylon sat on the banks of which river?', '["Tigris","Euphrates","Nile","Jordan"]'::jsonb, 1),
    ('The two rivers that frame Mesopotamia are the Tigris and the?', '["Euphrates","Karun","Orontes","Indus"]'::jsonb, 0),
    ('‘Mesopotamia’ roughly means the land between the?', '["Mountains","Rivers","Seas","Deserts"]'::jsonb, 1),
    ('Karbala is best known for the shrine of which figure?', '["Imam Ali","Imam Husayn","Imam al-Jawad","Prophet Job"]'::jsonb, 1),
    ('The Al-Abbas Shrine in Karbala honours the brother of whom?', '["Imam Ali","Imam Husayn","Nebuchadnezzar","Hammurabi"]'::jsonb, 1),
    ('Karbala draws millions of pilgrims chiefly due to events tied to?', '["A trade fair","Imam Husayn’s martyrdom","A royal coronation","An eclipse"]'::jsonb, 1),
    ('The shrines of Karbala are noted for domes plated in?', '["Silver","Gold","Bronze","Copper"]'::jsonb, 1),
    ('Imam Husayn was a grandson of which prophet?', '["Abraham","Prophet Muhammad","Moses","Job"]'::jsonb, 1),
    ('The interiors of Karbala’s shrines are famous for intricate?', '["Mosaic floors","Mirror-work","Frescoes","Stained glass"]'::jsonb, 1),
    ('The Imam Ali Shrine is located in which city?', '["Kufa","Najaf","Karbala","Basra"]'::jsonb, 1),
    ('The world’s largest cemetery, Wadi Al-Salam, lies in which city?', '["Mosul","Najaf","Samarra","Ur"]'::jsonb, 1),
    ('Najaf’s seminary, the intellectual heart of Shia study, is the?', '["Diwan","Hawza","Madrasa al-Mustansiriya","Bayt al-Hikma"]'::jsonb, 1),
    ('Imam Ali ruled the Islamic caliphate from which city?', '["Baghdad","Kufa","Basra","Samarra"]'::jsonb, 1),
    ('The Great Mosque of Kufa is counted among the world’s?', '["Largest mosques","Oldest mosques","Newest mosques","Smallest mosques"]'::jsonb, 1),
    ('Maytham al-Tammar was a devoted companion of whom?', '["Imam Husayn","Imam Ali","Nebuchadnezzar","Gilgamesh"]'::jsonb, 1),
    ('To the Shia, Imam Ali was the first what?', '["Caliph of Baghdad","Leader of the faithful (Imam)","King of Babylon","Prophet"]'::jsonb, 1),
    ('‘Wadi Al-Salam’ translates roughly as the Valley of?', '["Kings","Peace","Palms","Rivers"]'::jsonb, 1),
    ('The dome of the Imam Ali Shrine in Najaf is famously?', '["Blue","Golden","Green","White"]'::jsonb, 1),
    ('Kufa once served as the capital of the caliphate under?', '["Imam Ali","Harun al-Rashid","Cyrus","Sargon"]'::jsonb, 0),
    ('Uruk is celebrated as the birthplace of what?', '["Glassmaking","Writing","Coinage","Paper"]'::jsonb, 1),
    ('The earliest writing system to emerge in Mesopotamia is called?', '["Hieroglyphics","Cuneiform","Linear B","Runes"]'::jsonb, 1),
    ('Cuneiform was typically written using a stylus pressed into?', '["Papyrus","Clay tablets","Stone slabs","Animal hide"]'::jsonb, 1),
    ('The Ziggurat of Ur was built by which ancient civilization?', '["The Sumerians","The Romans","The Mongols","The Greeks"]'::jsonb, 0),
    ('A ziggurat is best described as an ancient?', '["Tomb","Stepped temple tower","Aqueduct","Harbour"]'::jsonb, 1),
    ('Uruk is often described as one of the world’s first what?', '["Ports","Cities","Libraries","Universities"]'::jsonb, 1),
    ('The legendary king tied to Uruk in the oldest epic is?', '["Hammurabi","Gilgamesh","Nebuchadnezzar","Sargon"]'::jsonb, 1),
    ('The Ziggurat of Ur was dedicated to which moon god?', '["Marduk","Nanna","Nabu","Shamash"]'::jsonb, 1),
    ('Uruk and Ur both flourished in which southern region?', '["Assyria","Sumer","Phoenicia","Nubia"]'::jsonb, 1),
    ('The first cuneiform marks were pressed with pens made from?', '["Bronze","Reeds","Bone","Gold"]'::jsonb, 1),
    ('The Mesopotamian Marshes are sometimes called the Venice of the?', '["North","Middle East","Mediterranean","Caucasus"]'::jsonb, 1),
    ('Traditional arched reed guesthouses in the marshes are called?', '["Yurts","Mudhif","Riads","Dachas"]'::jsonb, 1),
    ('The marshes are popularly linked to the legend of the Garden of?', '["Babylon","Eden","Hesperides","Avalon"]'::jsonb, 1),
    ('Marsh communities have traditionally travelled mainly by?', '["Camel","Boat","Rail","Horse"]'::jsonb, 1),
    ('The dwellings of the marshes are built primarily from?', '["Stone","Reeds","Brick","Timber planks"]'::jsonb, 1),
    ('The people who inhabit the Mesopotamian Marshes are often called the?', '["Bedouin","Marsh Arabs","Kurds","Assyrians"]'::jsonb, 1),
    ('The Mesopotamian Marshes lie mainly in which part of Iraq?', '["The north","The south","The far west","The central highlands"]'::jsonb, 1),
    ('Basra is historically known as Iraq’s major southern?', '["Mining town","Port city","Mountain resort","Capital"]'::jsonb, 1),
    ('Basra’s traditional carved wooden bay-window architecture is called?', '["Mashrabiya only","Shanasheel","Iwan","Stucco"]'::jsonb, 1),
    ('The Shanasheel style is associated especially with which era in Basra?', '["Sumerian era","Ottoman era","Stone Age","Mongol era"]'::jsonb, 1),
    ('Basra historically connected Iraq with India, Africa and the?', '["Baltic Sea","Persian Gulf","Atlantic","Caspian Sea"]'::jsonb, 1),
    ('Basra is home to historic churches of which Christian community?', '["Coptic","Armenian","Ethiopian","Maronite"]'::jsonb, 1),
    ('The Basra Museum displays artifacts from Mesopotamian, Islamic and modern?', '["Persian history","Iraqi history","Egyptian history","Greek history"]'::jsonb, 1),
    ('Beyond trade, Basra was also historically a centre of?', '["Mining","Intellectual production and learning","Shipbuilding only","Pearl diving only"]'::jsonb, 1),
    ('The spiral Malwiya Minaret is located in which city?', '["Mosul","Samarra","Najaf","Ur"]'::jsonb, 1),
    ('The Malwiya Minaret’s spiral form was inspired by ancient?', '["Pyramids","Ziggurats","Lighthouses","Obelisks"]'::jsonb, 1),
    ('Samarra once served as the capital of which dynasty?', '["The Sumerians","The Abbasids","The Assyrians","The Parthians"]'::jsonb, 1),
    ('The Al-Askari Shrine in Samarra has an iconic dome of?', '["Blue tile","Gold","Green copper","Plain stone"]'::jsonb, 1),
    ('The Al-Askari Shrine is the resting place of Imam Ali al-Hadi and Imam?', '["Musa al-Kadhim","Hasan al-Askari","al-Jawad","Husayn"]'::jsonb, 1),
    ('Samarra was built as a new centre of power along which river?', '["Euphrates","Tigris","Diyala","Khabur"]'::jsonb, 1),
    ('Mosul is affectionately nicknamed the City of Two?', '["Rivers","Springs","Towers","Bridges"]'::jsonb, 1),
    ('Mosul lies in which part of Iraq?', '["The north","The far south","The western desert","The marshes"]'::jsonb, 0),
    ('Mosul is especially noted for its multi-ethnic and multi-religious?', '["Cuisine only","History","Climate","Coastline"]'::jsonb, 1),
    ('Old Mosul is known for traditional crafts, food and?', '["Mining","Music","Surfing","Skiing"]'::jsonb, 1),
    ('Nimrud was once a capital of which empire?', '["The Neo-Assyrian Empire","The Roman Empire","The Mughal Empire","The Ottoman Empire"]'::jsonb, 0),
    ('Assyrian palaces were famous for protective carved wall?', '["Tapestries","Reliefs","Mosaics","Murals in oil"]'::jsonb, 1),
    ('The winged, human-headed bull guardians of Assyrian gates are called?', '["Sphinxes","Lamassu","Griffins","Cherubim"]'::jsonb, 1),
    ('The Assyrians were renowned for their intricate work in?', '["Glass","Stone carving","Silk","Porcelain"]'::jsonb, 1),
    ('Nimrud lies near which northern Iraqi city?', '["Basra","Mosul","Najaf","Karbala"]'::jsonb, 1),
    ('The Assyrian Empire is especially remembered for building massive?', '["Canals only","Palaces","Pyramids","Theatres"]'::jsonb, 1),
    ('Hatra is recognised internationally as a UNESCO World?', '["Biosphere","Heritage Site","Trade Zone","Capital"]'::jsonb, 1),
    ('Hatra was a desert fortress city between the Roman and which spheres?', '["Egyptian","Parthian","Greek","Mongol"]'::jsonb, 1),
    ('Hatra’s architecture is famous as a striking blend of?', '["Modern and Gothic","Eastern and Greco-Roman styles","Chinese and Indian","Norse and Celtic"]'::jsonb, 1),
    ('Hatra is best described as a fortified desert?', '["Tomb","City","Harbour","Mine"]'::jsonb, 1),
    ('Hatra’s stone structures survived largely thanks to the preserving?', '["Sea air","Desert","Forest","Glacier"]'::jsonb, 1),
    ('Hatra is admired for its grand arches and sculpted temple?', '["Domes","Columns","Minarets","Spires"]'::jsonb, 1),
    ('The shrines of Imam Musa al-Kadhim and al-Jawad are in which Baghdad district?', '["Karkh","Kadhimiya","Sadr City","Adhamiyah"]'::jsonb, 1),
    ('Baghdad was historically the capital of which caliphate?', '["The Umayyad","The Abbasid","The Fatimid","The Ottoman"]'::jsonb, 1),
    ('The Aqarquf Ziggurat near Baghdad was built by which people?', '["The Kassites","The Romans","The Greeks","The Phoenicians"]'::jsonb, 0),
    ('Baghdad sits on the banks of which river?', '["Euphrates","Tigris","Karun","Orontes"]'::jsonb, 1),
    ('Old Baghdad’s historic architecture reflects Ottoman and which colonial era?', '["French","British","Portuguese","Dutch"]'::jsonb, 1),
    ('The Kadhimiya shrines are noted for fine gold-leaf and?', '["Marble floors","Mirror-work","Stained glass","Frescoes"]'::jsonb, 1),
    ('Aqarquf is a ziggurat raised by which ancient dynasty?', '["Sumerian","Kassite","Parthian","Sassanid"]'::jsonb, 1),
    ('Baghdad today serves as Iraq’s?', '["Largest port","Capital","Chief seaside resort","Smallest town"]'::jsonb, 1),
    ('Iraq is widely celebrated as the cradle of what?', '["Industry","Civilization","Democracy","Cinema"]'::jsonb, 1),
    ('The Tigris-Euphrates valley has sustained human settlement for?', '["A few decades","Millennia","A single century","Ten years"]'::jsonb, 1),
    ('The tour begins with arrival at which airport?', '["Basra International","Baghdad International","Erbil International","Najaf International"]'::jsonb, 1),
    ('A central theme of the tour is contrasting ancient empires with living?', '["Sport","Faith and religious traditions","Industry","Fashion"]'::jsonb, 1),
    ('The civilization credited with inventing writing in southern Iraq was the?', '["Sumerians","Vikings","Aztecs","Zulu"]'::jsonb, 0),
    ('The Code of Hammurabi established an early precedent for legal?', '["Immunity","Accountability","Secrecy","Taxation"]'::jsonb, 1),
    ('The Neo-Babylonian Empire reached its height under which king?', '["Sargon","Nebuchadnezzar II","Darius","Trajan"]'::jsonb, 1),
    ('The world’s first true urban societies arose in which region?', '["Scandinavia","Mesopotamia","The Andes","Central Asia"]'::jsonb, 1),
    ('Marshes, ziggurats and shrines on this tour all lie within modern-day?', '["Iran","Iraq","Syria","Turkey"]'::jsonb, 1),
    ('The Code of Hammurabi is said to have influenced centuries of?', '["Navigation","Governance and law","Painting","Music"]'::jsonb, 1),
    ('Adam’s Tree is a symbolic site linked to local?', '["Industry","Tradition","Mining","Astronomy"]'::jsonb, 1),
    ('The Ishtar Gate dates to the reign of which king?', '["Ashurnasirpal","Nebuchadnezzar II","Cyrus","Hammurabi"]'::jsonb, 1),
    ('The largest cemetery in the world is named?', '["Wadi Al-Salam","Wadi Rum","Wadi Musa","Wadi Halfa"]'::jsonb, 0),
    ('The Hawza in Najaf is essentially a religious?', '["Hospital","Seminary","Marketplace","Fortress"]'::jsonb, 1),
    ('The Malwiya Minaret belongs to the Great Mosque of?', '["Kufa","Samarra","Najaf","Basra"]'::jsonb, 1),
    ('The seven-day tour concludes in which city?', '["Basra","Baghdad","Mosul","Karbala"]'::jsonb, 1)
) as v(question, options, correct_index)
where not exists (select 1 from public.quiz_questions);

-- ============================================================================
--  Done. Quick checks:
--    select count(*) from public.quiz_questions;   -- expect 100
--    select * from public.quiz_pool limit 3;       -- no correct answer column
--  To make someone admin manually:
--    update public.profiles set is_admin = true where email = 'you@example.com';
-- ============================================================================
