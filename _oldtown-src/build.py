# Builds the static, crawlable Baghdad Old Town pages (EN / AR / RU) from template.html.
# Run:  python3 _oldtown-src/build.py   (needs: pip install playwright && playwright install chromium)
# Output: baghdad-old-town.html (EN), ar/baghdad-old-town.html, ru/baghdad-old-town.html
import asyncio, json, re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TPL = ROOT / "_oldtown-src" / "template.html"
SITE = "https://discovery.fabletour.com"
URL = {"en": SITE + "/baghdad-old-town", "ar": SITE + "/ar/baghdad-old-town", "ru": SITE + "/ru/baghdad-old-town"}
OUT = {"en": ROOT / "baghdad-old-town.html", "ar": ROOT / "ar" / "baghdad-old-town.html", "ru": ROOT / "ru" / "baghdad-old-town.html"}
PATH = {"en": "/baghdad-old-town", "ar": "/ar/baghdad-old-town", "ru": "/ru/baghdad-old-town"}
IMG = SITE + "/mutanabbi-statue.webp"
VIDEO_ID = "BqSXeqqE9cI"
STOPS = ["Mustansiriyah Madrasah", "Copper Market (Souq al-Safafeer)", "Al-Baghdadi Museum",
         "Al Rasheed Street", "Mutanabbi Street", "Qishla Clock Tower"]
SAME_AS = ["https://www.instagram.com/fable_tour", "https://www.youtube.com/@fabletour",
           "https://www.tiktok.com/@fabletour", "https://www.getyourguide.com/fable-tour-in-iraq-s471675/",
           "https://iraq.fabletour.com/"]

META = {
"en": dict(
  locale="en_US",
  title="Baghdad Old Town Walking Tour — Private Guide, 6 Historic Stops | Fable Tour",
  desc="Private 4–5 hour walking tour of old Baghdad with a local guide: Mustansiriyah Madrasah, Safafeer Copper Market, Al-Baghdadi Museum, Al Rasheed Street, Mutanabbi Street & the Qishla. Hotel pickup and entry tickets included.",
  kw="Baghdad Old Town tour, Baghdad walking tour, things to do in Baghdad, Baghdad private guide, Mutanabbi Street, Mustansiriyah Madrasah, Qishla Baghdad, Safafeer copper market, Al Rasheed Street, Iraq tours, Baghdad day tour",
  og="Baghdad Old Town Private Walking Tour — A Journey Through the Heart of History",
  name="Baghdad Old Town Private Walking Tour",
  ldesc="A 4–5 hour private walking tour through historic Baghdad with a local guide, covering six stops: Mustansiriyah Madrasah, Safafeer Copper Market, Al-Baghdadi Museum, Al Rasheed Street, Mutanabbi Street and the Qishla Clock Tower. Hotel pickup and drop-off and all entry tickets included.",
  crumbs=["Fable Tour Discovery", "Baghdad Old Town Tour"],
  faqEyebrow="Good to know", faqTitle="Frequently asked questions",
  faq=[
    ("How long is the Baghdad Old Town tour and which places does it visit?",
     "The tour takes 4–5 hours on foot and visits six stops in historic Baghdad: the Mustansiriyah Madrasah, the Safafeer Copper Market, the Al-Baghdadi Museum, Al Rasheed Street, Mutanabbi Street and the Qishla Clock Tower."),
    ("What is included in the tour?",
     "A private local guide for your group only, hotel or house pickup and drop-off anywhere in Baghdad, and all entry tickets to the museums and sites on the route. Food, drinks and personal purchases are not included."),
    ("How much does the tour cost?",
     "The price depends on the number of guests. Choose your date and group size in the booking form on this page and your total price appears instantly, with entry tickets already included."),
    ("Do I have to pay online?",
     "No. No payment is taken online and no deposit is required. Send your booking request and we will confirm your date and pickup time by email or WhatsApp within a few hours."),
    ("Which languages does the guide speak?",
     "Tours are guided in English, Arabic or Russian — choose the language you prefer when you book."),
    ("What should I wear?",
     "Comfortable walking shoes and light, modest clothing that covers shoulders and knees. Mornings are the most pleasant time to walk, especially in summer, and we recommend bringing water and sun protection."),
  ]),
"ar": dict(
  locale="ar_IQ",
  title="جولة بغداد القديمة سيراً على الأقدام — دليل خاص و٦ معالم تاريخية | Fable Tour",
  desc="جولة خاصة ٤–٥ ساعات في بغداد القديمة مع دليل محلي: المدرسة المستنصرية، سوق الصفافير، المتحف البغدادي، شارع الرشيد، شارع المتنبي والقشلة. تشمل النقل من الفندق وجميع تذاكر الدخول.",
  kw="جولة بغداد القديمة, جولة سياحية في بغداد, شارع المتنبي, المدرسة المستنصرية, القشلة, سوق الصفافير, شارع الرشيد, المتحف البغدادي, دليل سياحي بغداد, سياحة العراق, أماكن سياحية في بغداد",
  og="جولة بغداد القديمة الخاصة — رحلة في قلب التاريخ",
  name="جولة بغداد القديمة الخاصة سيراً على الأقدام",
  ldesc="جولة خاصة لمدة ٤–٥ ساعات سيراً على الأقدام في بغداد التاريخية مع دليل محلي، تشمل ست محطات: المدرسة المستنصرية، سوق الصفافير، المتحف البغدادي، شارع الرشيد، شارع المتنبي وساعة القشلة. تشمل النقل من الفندق وإليه وجميع تذاكر الدخول.",
  crumbs=["Fable Tour Discovery", "جولة بغداد القديمة"],
  faqEyebrow="معلومات مهمة", faqTitle="الأسئلة الشائعة",
  faq=[
    ("كم تستغرق جولة بغداد القديمة وما الأماكن التي تزورها؟",
     "تستغرق الجولة ٤–٥ ساعات سيراً على الأقدام وتزور ست محطات في بغداد التاريخية: المدرسة المستنصرية، سوق الصفافير، المتحف البغدادي، شارع الرشيد، شارع المتنبي وساعة القشلة."),
    ("ماذا تشمل الجولة؟",
     "دليل محلي خاص لمجموعتك فقط، النقل من الفندق أو المنزل وإليه في أي مكان ببغداد، وجميع تذاكر الدخول إلى المتاحف والمواقع على المسار. لا تشمل الطعام والمشروبات والمشتريات الشخصية."),
    ("كم سعر الجولة؟",
     "يعتمد السعر على عدد الأشخاص. اختر التاريخ وعدد الأشخاص في نموذج الحجز بهذه الصفحة ويظهر لك السعر الكلي فوراً، شاملاً تذاكر الدخول."),
    ("هل يجب أن أدفع عبر الإنترنت؟",
     "لا. لا يُدفع أي مبلغ عبر الإنترنت ولا يوجد عربون. أرسل طلب الحجز وسنؤكد لك التاريخ ووقت الاستلام عبر البريد أو الواتساب خلال ساعات."),
    ("بأي لغة يتحدث الدليل؟",
     "تتوفر الجولة باللغة العربية أو الإنكليزية أو الروسية — اختر اللغة التي تفضلها عند الحجز."),
    ("ماذا ألبس في الجولة؟",
     "حذاء مريح للمشي وملابس خفيفة ومحتشمة تغطي الكتفين والركبتين. الصباح هو أفضل وقت للمشي خاصة في الصيف، وننصح بإحضار الماء وواقي الشمس."),
  ]),
"ru": dict(
  locale="ru_RU",
  title="Экскурсия по Старому Багдаду — частный гид, 6 исторических мест | Fable Tour",
  desc="Частная пешеходная экскурсия по старому Багдаду на 4–5 часов с местным гидом: медресе Мустансирия, медный рынок Сафафир, Багдадский музей, улица Рашид, улица Мутанабби и Кишла. Трансфер из отеля и входные билеты включены.",
  kw="экскурсия Багдад, Старый Багдад, что посмотреть в Багдаде, гид в Багдаде, улица Мутанабби, медресе Мустансирия, Кишла, рынок Сафафир, туры в Ирак, Ирак туризм, экскурсия по Багдаду на русском",
  og="Частная экскурсия по Старому Багдаду — путешествие в сердце истории",
  name="Частная пешеходная экскурсия по Старому Багдаду",
  ldesc="Частная пешеходная экскурсия на 4–5 часов по историческому Багдаду с местным гидом: медресе Мустансирия, медный рынок Сафафир, Багдадский музей, улица Рашид, улица Мутанабби и часовая башня Кишла. Трансфер из отеля и обратно и все входные билеты включены.",
  crumbs=["Fable Tour Discovery", "Экскурсия по Старому Багдаду"],
  faqEyebrow="Полезно знать", faqTitle="Частые вопросы",
  faq=[
    ("Сколько длится экскурсия по Старому Багдаду и что мы посетим?",
     "Экскурсия длится 4–5 часов пешком и включает шесть мест исторического Багдада: медресе Мустансирия, медный рынок Сафафир, Багдадский музей, улицу Рашид, улицу Мутанабби и часовую башню Кишла."),
    ("Что входит в стоимость?",
     "Частный местный гид только для вашей группы, трансфер из отеля или дома и обратно в пределах Багдада и все входные билеты в музеи и на объекты маршрута. Еда, напитки и личные покупки не включены."),
    ("Сколько стоит экскурсия?",
     "Цена зависит от количества гостей. Выберите дату и размер группы в форме бронирования на этой странице — итоговая цена появится сразу, входные билеты уже включены."),
    ("Нужно ли платить онлайн?",
     "Нет. Онлайн-оплата и предоплата не требуются. Отправьте заявку, и в течение нескольких часов мы подтвердим дату и время трансфера по почте или в WhatsApp."),
    ("На каком языке говорит гид?",
     "Экскурсия проводится на русском, английском или арабском языке — выберите удобный язык при бронировании."),
    ("Как одеться на экскурсию?",
     "Удобная обувь для ходьбы и лёгкая скромная одежда, закрывающая плечи и колени. Утро — самое приятное время для прогулки, особенно летом; возьмите с собой воду и защиту от солнца."),
  ]),
}

def esc(t): return html.escape(t, quote=True)

def head_block(lang):
    m = META[lang]
    alts = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{URL[l]}">' for l in ("en", "ar", "ru"))
    alts += f'\n<link rel="alternate" hreflang="x-default" href="{URL["en"]}">'
    other_locales = "\n".join(f'<meta property="og:locale:alternate" content="{META[l]["locale"]}">' for l in ("en", "ar", "ru") if l != lang)
    graph = [
      {"@type": "TouristTrip", "@id": URL[lang] + "#tour", "name": m["name"], "description": m["ldesc"],
       "url": URL[lang], "image": [IMG, SITE + "/qishla-arcade.webp", SITE + "/shabandar-cafe-tea.webp"],
       "inLanguage": lang, "touristType": ["Cultural tourism", "Heritage tourism"],
       "itinerary": {"@type": "ItemList", "numberOfItems": len(STOPS),
                     "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                          "item": {"@type": "TouristAttraction", "name": n,
                                                   "address": {"@type": "PostalAddress", "addressLocality": "Baghdad", "addressCountry": "IQ"}}}
                                         for i, n in enumerate(STOPS)]},
       "provider": {"@id": SITE + "/#org"}},
      {"@type": "TravelAgency", "@id": SITE + "/#org", "name": "Fable Tour", "url": SITE,
       "logo": "https://iraq.fabletour.com/logo.png", "image": IMG, "telephone": "+964 771 174 5353",
       "email": "support@fabletour.com",
       "address": {"@type": "PostalAddress", "streetAddress": "Baghdad International Airport", "addressLocality": "Baghdad",
                   "addressRegion": "Al-Karkh", "addressCountry": "IQ"},
       "areaServed": "Iraq", "sameAs": SAME_AS},
      {"@type": "BreadcrumbList", "itemListElement": [
         {"@type": "ListItem", "position": 1, "name": m["crumbs"][0], "item": SITE + "/"},
         {"@type": "ListItem", "position": 2, "name": m["crumbs"][1], "item": URL[lang]}]},
      {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q,
          "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in m["faq"]]},
    ]
    if lang == "en":
        graph.append({"@type": "VideoObject", "name": "Baghdad Old Town walking tour with Fable Tour",
                      "description": "A walk through old Baghdad with Fable Tour — Mutanabbi Street, the Qishla, the Copper Market and more.",
                      "thumbnailUrl": f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg",
                      "embedUrl": f"https://www.youtube.com/embed/{VIDEO_ID}",
                      "contentUrl": f"https://www.youtube.com/watch?v={VIDEO_ID}"})
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
    return f'''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="only light">
<title>{esc(m["title"])}</title>
<meta name="description" content="{esc(m["desc"])}">
<meta name="keywords" content="{esc(m["kw"])}">
<meta name="author" content="Fable Tour">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="geo.region" content="IQ-BG"><meta name="geo.placename" content="Baghdad">
<link rel="canonical" href="{URL[lang]}">
{alts}
<link rel="icon" href="/favicon.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" as="image" href="/mutanabbi-statue.webp" fetchpriority="high">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Fable Tour">
<meta property="og:title" content="{esc(m["og"])}">
<meta property="og:description" content="{esc(m["desc"])}">
<meta property="og:url" content="{URL[lang]}">
<meta property="og:image" content="{IMG}">
<meta property="og:image:alt" content="{esc(m["og"])}">
<meta property="og:locale" content="{m["locale"]}">
{other_locales}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(m["og"])}">
<meta name="twitter:description" content="{esc(m["desc"])}">
<meta name="twitter:image" content="{IMG}">
<script type="application/ld+json">
{ld}
</script>
'''

def faq_section(lang):
    m = META[lang]
    items = "\n".join(f'      <details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in m["faq"])
    return f'''<section id="faq">
  <div class="wrap">
    <div class="section-head">
      <span class="eyebrow">{esc(m["faqEyebrow"])}</span>
      <h2>{esc(m["faqTitle"])}</h2>
    </div>
    <div class="faq">
{items}
    </div>
  </div>
</section>

'''

STUB = "window.supabase={createClient:()=>({rpc:async()=>({data:[],error:null}),from:()=>({insert:async()=>({error:null})})})}"

async def render():
    from playwright.async_api import async_playwright
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for lang in ("en", "ar", "ru"):
            pg = await b.new_page()
            await pg.route(re.compile(r"^https?://"), lambda r: r.abort())
            await pg.add_init_script(STUB)
            await pg.goto(TPL.as_uri())
            await pg.evaluate(f"""(lang)=>{{
              applyLang(lang);
              const v=document.getElementById('yt-en');
              if(lang==='en') v.removeAttribute('hidden'); else v.remove();
              document.getElementById('date-hint').textContent=I18N[lang].form.hint;
              document.getElementById('wa-float').classList.remove('show');
            }}""", lang)
            out[lang] = await pg.evaluate("document.documentElement.outerHTML")
            await pg.close()
        await b.close()
    return out

def finish(lang, doc):
    s = "<!DOCTYPE html>\n" + doc
    s = re.sub(r"<head>.*?(<link rel=\"preconnect\")", lambda mm: "<head>\n" + head_block(lang) + mm.group(1), s, count=1, flags=re.S)
    assert "application/ld+json" in s and s.count("<title>") == 1
    # language switcher -> real links
    names = {"en": "EN", "ar": "ع", "ru": "РУ"}
    links = "".join(f'<a href="{PATH[l]}" hreflang="{l}" lang="{l}"{" class=\"on\" aria-current=\"page\"" if l == lang else ""}>{names[l]}</a>' for l in ("en", "ar", "ru"))
    s = re.sub(r'(<div class="langs"[^>]*>).*?(</div>)', lambda mm: mm.group(1) + links + mm.group(2), s, count=1, flags=re.S)
    # FAQ before booking
    s = s.replace('<section class="alt" id="book">', faq_section(lang) + '<section class="alt" id="book">', 1)
    # fixed language per page
    s = re.sub(r"let LANG = 'en';\ntry\{[^\n]*\}catch\(e\)\{\}", f"let LANG = '{lang}';", s, count=1)
    s = s.replace("  try{ localStorage.setItem('ft_lang', lang); }catch(e){}\n", "")
    s = s.replace("  document.getElementById('yt-en').hidden = (lang !== 'en');\n",
                  "  const yt=document.getElementById('yt-en'); if(yt) yt.hidden = (lang !== 'en');\n")
    # gallery is already in the HTML
    s = s.replace("  if(!GALLERY_IMAGES.length){", "  if(grid.children.length) return;\n  if(!GALLERY_IMAGES.length){", 1)
    # absolute asset paths (pages live in sub-folders too)
    s = s.replace('src="./', 'src="/').replace('"./', '"/')
    assert f"let LANG = '{lang}';" in s and "grid.children.length" in s
    return s

def main():
    docs = asyncio.run(render())
    for lang, doc in docs.items():
        OUT[lang].parent.mkdir(exist_ok=True)
        OUT[lang].write_text(finish(lang, doc), encoding="utf-8")
        print("wrote", OUT[lang].relative_to(ROOT))

if __name__ == "__main__":
    main()
