# Fable Tour Discovery

A seven-day luxury cultural tour of Iraq — itinerary, day histories, a timed quiz,
a leaderboard, an admin dashboard, and a WhatsApp button. Front-end is a single
`index.html`; the backend is Supabase (auth, media storage, quiz, leaderboard).

## Files in this repo

- `index.html` — the website (this is what visitors see). Must keep this name.
- `supabase-schema.sql` — run this once in Supabase to create the database.
- `.nojekyll` — tells GitHub Pages to serve files exactly as-is.

---

## 1. Put the site on GitHub Pages

1. Create a new GitHub repository (Public).
2. Upload all the files in this folder to the repository **root** (the
   `Add file -> Upload files` button works from your phone or computer).
   Make sure `index.html` sits at the top level, not inside a sub-folder.
3. In the repo, go to **Settings -> Pages**.
4. Under **Build and deployment -> Source**, choose **Deploy from a branch**.
5. Branch: **main**, folder: **/ (root)**. Save.
6. Wait ~1 minute, then refresh. Pages shows your live URL, e.g.
   `https://YOUR-USERNAME.github.io/YOUR-REPO/`

That URL is your live website.

---

## 2. Set up the database (Supabase)

1. In your Supabase project, open **SQL Editor**.
2. Paste the entire contents of `supabase-schema.sql` and click **Run**.
   This creates the tables, security rules, the `media` storage bucket, the quiz
   functions, and loads all 100 quiz questions.
3. Open **Authentication -> URL Configuration** and set:
   - **Site URL** = your GitHub Pages URL from step 1.
   - Add the same URL under **Redirect URLs** (so password-reset links work).
4. (Optional, makes testing easier) **Authentication -> Providers -> Email** and
   turn **Confirm email** OFF so new accounts can sign in immediately. If you
   leave it ON, every new account must click an email confirmation link first.

The site is already wired to your project (URL and publishable key are inside
`index.html`). The publishable key is safe to be public; security comes from the
rules in the SQL file.

---

## 3. Become the admin

1. Open your live site, tap the menu, choose **Sign in -> Sign up** tab.
2. Sign up with email **support@fabletour.com** (this email is auto-marked as
   admin by the database). Confirm the email if confirmation is ON.
3. Sign in. A **Dashboard** link appears, where you upload photos/videos for each
   page and review sign-ups.

To use a different admin email, change `support@fabletour.com` in both
`index.html` (the `ADMIN_EMAILS` / `SUPPORT_EMAIL` area) and in
`supabase-schema.sql`, then re-run the SQL.

---

## Security note

Never commit your Supabase **secret key** (`sb_secret_...`) to this repo or share
it anywhere. Only the **publishable key** belongs in the browser. If a secret key
was ever exposed, rotate it in Supabase -> Settings -> API Keys.

## Optional: use your own domain (fabletour.com)

In repo **Settings -> Pages -> Custom domain**, add `fabletour.com` and follow the
DNS instructions. Then update the Supabase Site URL to match. The SEO tags in
`index.html` already reference `https://fabletour.com/`.
