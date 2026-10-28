#!/usr/bin/env python3
"""
Babylon Day Trip — multilingual static page generator (Fable Tour)

Source  : _babylon-src/template.html  +  _babylon-src/i18n/<lang>.json
Output  : /babylon-tour.html                 (Arabic, original URL)
          /babylon-day-trip/<slug>/index.html (every other language)
          + updates the Babylon block inside /sitemap.xml

Run from the repo root:   python3 _babylon-src/build.py
"""
import json, html, re, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_babylon-src")
SITE = "https://discovery.fabletour.com"
ORDER = ["ar", "en", "ru", "de", "fr", "es", "it", "el", "cs", "pl",
         "zh-Hans", "ja", "tr", "fa", "ms", "id", "th"]
X_DEFAULT = "en"
PRICE = "336000"
IMG_JPG = SITE + "/IMG_8878.jpeg"
IMG_W, IMG_H = 1284, 934
TODAY = datetime.date.today().isoformat()

SAME_AS = [
    "https://www.instagram.com/fable_tour/",
    "https://www.youtube.com/@fabletour",
    "https://www.tiktok.com/@fabletour",
    "https://www.getyourguide.com/fable-tour-in-iraq-s471675/",
    "https://iraq.fabletour.com/",
]

# Google Fonts per language. Latin brand faces (Marcellus + Jost) are always loaded.
BASE_FONTS = "family=Libre+Baskerville:wght@400;700&family=Inter+Tight:wght@400;500;600;700"
FONTS = {
    "ar": "family=Amiri:wght@400;700&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700",
    "fa": "family=Amiri:ital,wght@0,400;0,700&family=Vazirmatn:wght@300;400;500;700",
    "ru": "family=PT+Serif:wght@400;700",
    "el": "family=Noto+Serif:ital,wght@0,400;0,600;1,400&family=Noto+Sans:wght@300;400;500",
    "zh-Hans": "family=Noto+Serif+SC:wght@400;600&family=Noto+Sans+SC:wght@300;400;500",
    "ja": "family=Noto+Serif+JP:wght@400;600&family=Noto+Sans+JP:wght@300;400;500",
    "th": "family=Noto+Serif+Thai:wght@400;600&family=Noto+Sans+Thai:wght@300;400;500",
}
# Per-language font variables (non-Latin scripts reuse the ru/ar rule sets of the template)
FONT_VARS = {
    "fa": '--f-ar-disp:"Amiri",serif;--f-ar-body:"Vazirmatn",sans-serif;--f-body:"Vazirmatn",sans-serif;',
    "el": '--f-ru-disp:"Noto Serif",serif;--f-ru-body:"Noto Serif",serif;--f-body:"Noto Sans",sans-serif;--f-disp:"Noto Serif",serif;',
    "zh-Hans": '--f-ru-disp:"Noto Serif SC",serif;--f-ru-body:"Noto Sans SC",sans-serif;--f-body:"Noto Sans SC",sans-serif;--f-disp:"Noto Serif SC",serif;',
    "ja": '--f-ru-disp:"Noto Serif JP",serif;--f-ru-body:"Noto Sans JP",sans-serif;--f-body:"Noto Sans JP",sans-serif;--f-disp:"Noto Serif JP",serif;',
    "th": '--f-ru-disp:"Noto Serif Thai",serif;--f-ru-body:"Noto Sans Thai",sans-serif;--f-body:"Noto Sans Thai",sans-serif;--f-disp:"Noto Serif Thai",serif;',
}
AR_LIKE = {"fa"}                       # reuse html[lang="ar"] rules
RU_LIKE = {"el", "zh-Hans", "ja", "th"}  # reuse html[lang="ru"] rules

E = lambda s: html.escape(str(s), quote=True)


def url_of(L):
    return SITE + "/babylon-tour.html" if L["code"] == "ar" else f'{SITE}/babylon-day-trip/{L["slug"]}/'


def load():
    langs = {}
    for c in ORDER:
        with open(os.path.join(SRC, "i18n", c + ".json"), encoding="utf-8") as f:
            langs[c] = json.load(f)
    return langs


def head_seo(L, langs):
    s = L["seo"]
    u = url_of(L)
    out = [
        f'<title>{E(s["title"])}</title>',
        f'<meta name="description" content="{E(s["description"])}">',
        f'<meta name="keywords" content="{E(s["keywords"])}">',
        '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
        '<meta name="author" content="Fable Tour">',
        f'<link rel="canonical" href="{u}">',
    ]
    for c in ORDER:
        out.append(f'<link rel="alternate" hreflang="{c}" href="{url_of(langs[c])}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{url_of(langs[X_DEFAULT])}">')
    out += [
        '<link rel="icon" type="image/png" href="/favicon.png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        '<link rel="preload" as="image" href="/IMG_8878.webp" type="image/webp" fetchpriority="high">',
        '<meta name="geo.region" content="IQ-BB">',
        '<meta name="geo.placename" content="Babylon, Iraq">',
        '<meta name="geo.position" content="32.5422;44.4210">',
        '<meta name="ICBM" content="32.5422, 44.4210">',
        '',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Fable Tour">',
        f'<meta property="og:locale" content="{L["og_locale"]}">',
    ]
    for c in ORDER:
        if c != L["code"]:
            out.append(f'<meta property="og:locale:alternate" content="{langs[c]["og_locale"]}">')
    out += [
        f'<meta property="og:url" content="{u}">',
        f'<meta property="og:title" content="{E(s["og_title"])}">',
        f'<meta property="og:description" content="{E(s["description"])}">',
        f'<meta property="og:image" content="{IMG_JPG}">',
        f'<meta property="og:image:secure_url" content="{IMG_JPG}">',
        '<meta property="og:image:type" content="image/jpeg">',
        f'<meta property="og:image:width" content="{IMG_W}">',
        f'<meta property="og:image:height" content="{IMG_H}">',
        f'<meta property="og:image:alt" content="{E(s["img_alt"])}">',
        '',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{E(s["og_title"])}">',
        f'<meta name="twitter:description" content="{E(s["description"])}">',
        f'<meta name="twitter:image" content="{IMG_JPG}">',
        f'<meta name="twitter:image:alt" content="{E(s["img_alt"])}">',
        '',
        '<meta name="theme-color" content="#1B2A47">',
        '<script type="application/ld+json">' + json.dumps(schema(L, langs), ensure_ascii=False).replace("</", "<\\/") + '</script>',
    ]
    return "\n".join(out)


def schema(L, langs):
    s, t = L["seo"], L["t"]
    u = url_of(L)
    org = {
        "@type": "TravelAgency", "@id": SITE + "/#fabletour", "name": "Fable Tour",
        "url": SITE + "/", "logo": SITE + "/favicon.png", "image": IMG_JPG,
        "telephone": "+9647711745353", "email": "support@fabletour.com", "priceRange": "$$",
        "address": {"@type": "PostalAddress", "streetAddress": "Baghdad International Airport, Al-Karkh",
                    "addressLocality": "Baghdad", "addressCountry": "IQ"},
        "sameAs": SAME_AS,
    }
    place = {
        "@type": ["TouristAttraction", "LandmarksOrHistoricalBuildings"],
        "name": s["attraction"],
        "description": t["stop1.lead"],
        "sameAs": ["https://whc.unesco.org/en/list/278", "https://en.wikipedia.org/wiki/Babylon"],
        "geo": {"@type": "GeoCoordinates", "latitude": 32.5422, "longitude": 44.4210},
        "address": {"@type": "PostalAddress", "addressRegion": "Babylon Governorate", "addressCountry": "IQ"},
    }
    trip = {
        "@type": "TouristTrip", "@id": u + "#trip", "name": s["trip_name"], "description": s["description"],
        "url": u, "image": [IMG_JPG], "inLanguage": L["code"],
        "touristType": ["Cultural tourism", "Archaeology", "Heritage tourism", "History"],
        "itinerary": {"@type": "ItemList", "numberOfItems": 1,
                      "itemListElement": [{"@type": "ListItem", "position": 1, "item": place}]},
        "provider": {"@id": SITE + "/#fabletour"},
    }
    page = {
        "@type": "WebPage", "@id": u + "#webpage", "url": u, "name": s["title"], "description": s["description"],
        "inLanguage": L["code"], "isPartOf": {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/", "name": "Fable Tour"},
        "primaryImageOfPage": {"@type": "ImageObject", "url": IMG_JPG, "width": IMG_W, "height": IMG_H},
        "about": {"@id": u + "#trip"}, "dateModified": TODAY,
        "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Fable Tour", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": s["breadcrumb"], "item": u}]},
    }
    faq = {"@type": "FAQPage", "@id": u + "#faq", "inLanguage": L["code"], "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in L["faq"]["items"]]}
    graph = [org, page, trip, faq]
    v = L.get("video")
    if v:
        graph.append({"@type": "VideoObject", "@id": u + "#video", "name": v["title"],
                      "description": s["description"], "inLanguage": L["code"],
                      "thumbnailUrl": f'https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg',
                      "embedUrl": f'https://www.youtube.com/embed/{v["id"]}',
                      "contentUrl": f'https://www.youtube.com/watch?v={v["id"]}'})
    return {"@context": "https://schema.org", "@graph": graph}


# Internal links to the other tour pages (languages that have them)
MORE_TOURS = {
    "en": ("More tours", [("Baghdad Old Town walking tour", "/baghdad-old-town"), ("Iraq tour programs", "https://iraq.fabletour.com/en/")]),
    "ar": ("جولات أخرى", [("جولة بغداد القديمة", "/ar/baghdad-old-town"), ("برامج العراق السياحية", "https://iraq.fabletour.com/")]),
    "ru": ("Другие туры", [("Экскурсия по Старому Багдаду", "/ru/baghdad-old-town"), ("Туры по Ираку", "https://iraq.fabletour.com/ru/")]),
}


def more_tours(L):
    m = MORE_TOURS.get(L["code"])
    if not m:
        return ""
    links = " · ".join(f'<a href="{u}">{E(t)}</a>' for t, u in m[1])
    return f'<p class="more-tours">{E(m[0])}: {links}</p>'


def lang_switch(L, langs):
    items = []
    for c in ORDER:
        o = langs[c]
        cur = ' aria-current="page" class="on"' if c == L["code"] else ""
        items.append(f'<li><a href="{url_of(o).replace(SITE, "")}" hreflang="{c}" lang="{c}"{cur}>'
                     f'<span>{E(o["native"])}</span><b>{E(o["short"])}</b></a></li>')
    globe = ('<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c2.6 2.8 3.9 6 3.9 9.5S14.6 18.7 12 21.5M12 2.5C9.4 5.3 8.1 8.5 8.1 12s1.3 6.7 3.9 9.5"/></svg>')
    return (f'<details class="lang-dd"><summary aria-label="Language / اللغة">{globe}<span>{E(L["short"])}</span>'
            f'<i class="chev" aria-hidden="true"></i></summary><ul class="lang-list">{"".join(items)}</ul></details>')


def video(L):
    v = L.get("video")
    if not v:
        return ""
    vid = v["id"]
    return f'''<!-- ░░ VIDEO ░░ -->
<section class="section vid-sec" id="video">
  <div class="container reveal">
    <div class="head">
      <span class="label">{E(v["kicker"])}</span>
      <h2>{E(v["title"])}</h2>
    </div>
    <div class="vwrap">
      <button class="vthumb" type="button" data-yt="{vid}" aria-label="▶ {E(v["title"])}">
        <img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="{E(v["title"])}" loading="lazy" decoding="async" width="480" height="360">
        <span class="vplay" aria-hidden="true"></span>
      </button>
    </div>
  </div>
</section>

'''


def faq(L):
    f = L["faq"]
    items = "\n".join(f'      <details class="faq-item"><summary><h3>{E(q)}</h3></summary><p>{E(a)}</p></details>'
                      for q, a in f["items"])
    return f'''<!-- ░░ FAQ ░░ -->
<section class="section faq" id="faq">
  <div class="container reveal">
    <div class="head">
      <span class="label">{E(f["kicker"])}</span>
      <h2>{E(f["title"])}</h2>
    </div>
    <div class="faq-list">
{items}
    </div>
  </div>
</section>
'''


EXTRA_CSS_COMMON = r'''
/* ───────────── language dropdown ───────────── */
.lang-dd{position:relative}
.lang-dd summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:.45rem;
  color:var(--champ-lt);font-family:var(--f-body);font-size:.78rem;letter-spacing:.14em;
  padding:.4rem .7rem;border:1px solid var(--hair);border-radius:999px;background:rgba(247,243,232,.7);
  -webkit-user-select:none;user-select:none;transition:.3s}
.lang-dd summary::-webkit-details-marker{display:none}
.lang-dd summary:hover{border-color:var(--champ)}
.lang-dd .chev{width:6px;height:6px;border-inline-end:1px solid currentColor;border-block-end:1px solid currentColor;
  transform:rotate(45deg) translateY(-2px);transition:.3s}
.lang-dd[open] .chev{transform:rotate(-135deg) translateY(-1px)}
.lang-list{list-style:none;position:absolute;inset-inline-end:0;top:calc(100% + .5rem);z-index:60;
  min-width:13.5rem;max-height:min(70vh,30rem);overflow:auto;padding:.4rem;
  background:#fbf8f0;border:1px solid var(--hair);border-radius:12px;box-shadow:0 18px 44px rgba(27,58,107,.18)}
.lang-list a{display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.55rem .8rem;
  border-radius:8px;color:var(--ivory);text-decoration:none;font-size:.95rem;line-height:1.3;font-style:normal;letter-spacing:0}
.lang-list a b{font-family:"Jost",sans-serif;font-weight:400;font-size:.68rem;letter-spacing:.14em;color:var(--muted)}
.lang-list a:hover,.lang-list a.on{background:rgba(168,132,47,.12)}
.lang-list a.on b{color:var(--champ-lt)}
.lang-list a span{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}

/* ───────────── video (click-to-load, no third-party cost until played) ───────────── */
.vid-sec .vwrap{position:relative;max-width:900px;margin:0 auto;aspect-ratio:16/9;border-radius:14px;
  overflow:hidden;box-shadow:0 18px 50px rgba(27,58,107,.28);background:#0d1b33}
.vid-sec iframe,.vthumb{position:absolute;inset:0;width:100%;height:100%;border:0}
.vthumb{cursor:pointer;padding:0;background:#0d1b33}
.vthumb img{width:100%;height:100%;object-fit:cover;display:block;opacity:.92;transition:.4s}
.vthumb:hover img{opacity:1;transform:scale(1.02)}
.vplay{position:absolute;left:50%;top:50%;width:76px;height:76px;margin:-38px 0 0 -38px;border-radius:50%;
  background:rgba(247,243,232,.92);box-shadow:0 8px 30px rgba(0,0,0,.35)}
.vplay::after{content:"";position:absolute;left:31px;top:24px;border-style:solid;border-width:14px 0 14px 22px;
  border-color:transparent transparent transparent var(--ivory)}

/* ───────────── FAQ ───────────── */
.faq-list{max-width:780px;margin:0 auto;border-block-start:1px solid var(--hair)}
.faq-item{border-block-end:1px solid var(--hair)}
.faq-item summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;
  gap:1.2rem;padding:1.3rem .2rem}
.faq-item summary::-webkit-details-marker{display:none}
.faq-item summary h3{font-size:1.18rem;font-weight:400;line-height:1.5;color:var(--ivory)}
.faq-item summary::after{content:"+";flex:none;color:var(--champ);font-size:1.5rem;line-height:1;transition:.3s}
.faq-item[open] summary::after{transform:rotate(45deg)}
.faq-item p{padding:0 .2rem 1.4rem;color:var(--ivory-soft);line-height:1.9}
'''

NO_ITALIC = '''
html[lang="{c}"] *{{font-style:normal !important}}
html[lang="{c}"] .label,html[lang="{c}"] .btn,html[lang="{c}"] .stop .meta,html[lang="{c}"] .spec .k,
html[lang="{c}"] .field label,html[lang="{c}"] .summary .row .k,html[lang="{c}"] .seat .nm,
html[lang="{c}"] .hero .place,html[lang="{c}"] .readmore,html[lang="{c}"] .cal .dow{{letter-spacing:{ls} !important}}
'''


def extra_css(L):
    c = L["code"]
    css = EXTRA_CSS_COMMON
    if c in FONT_VARS:
        css += ":root{" + FONT_VARS[c] + "}\n"
    if c in ("zh-Hans", "ja"):
        css += NO_ITALIC.format(c=c, ls=".08em")
        css += f'html[lang="{c}"] body{{line-height:1.95}}\n'
    if c == "th":
        css += NO_ITALIC.format(c=c, ls="0")
        css += 'html[lang="th"] *{letter-spacing:0 !important}\n'
    if c == "fa":
        css += 'html[lang="fa"] *{font-style:normal !important}\n'
    return css


EXTRA_JS = r'''
/* language dropdown: close on outside click / Esc */
(function(){const dd=document.querySelector(".lang-dd");if(!dd)return;
  document.addEventListener("click",e=>{if(dd.open&&!dd.contains(e.target))dd.removeAttribute("open");});
  document.addEventListener("keydown",e=>{if(e.key==="Escape")dd.removeAttribute("open");});})();
/* video facade → real player on click */
document.querySelectorAll(".vthumb[data-yt]").forEach(b=>b.addEventListener("click",()=>{
  const f=document.createElement("iframe");
  f.src="https://www.youtube-nocookie.com/embed/"+b.dataset.yt+"?autoplay=1&rel=0";
  f.title=b.getAttribute("aria-label")||"YouTube";
  f.allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
  f.referrerPolicy="strict-origin-when-cross-origin";f.allowFullscreen=true;b.replaceWith(f);
}));'''


def t_js(L):
    t = dict(L["t"])
    t["dir"] = L["dir"]
    wa = t.pop("wa_msg")
    wa = wa.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    for k in ("name", "date", "seats", "phone", "wa", "email"):
        wa = wa.replace("{" + k + "}", "${d." + k + "}")
    body = json.dumps(t, ensure_ascii=False, indent=1).replace("</", "<\\/")
    body = body[:body.rstrip().rfind("}")].rstrip() + ',\n "wa_msg":(d)=>`' + wa + '`\n}'
    return "{\n" + json.dumps(L["code"]) + ":" + body + "\n}"


def render(L, langs, tpl):
    c = L["code"]
    s = tpl
    # per-language CSS rule sets
    if c in AR_LIKE:
        s = s.replace('html[lang="ar"]', f'html[lang="{c}"]')
    if c in RU_LIKE:
        s = s.replace('html[lang="ru"]', f'html[lang="{c}"]')
    fonts = BASE_FONTS + ("&" + FONTS[c] if c in FONTS else "")
    hero = (f'<picture><source srcset="/IMG_8878.webp" type="image/webp">'
            f'<img src="/IMG_8878.jpeg" alt="{E(L["seo"]["img_alt"])}" width="{IMG_W}" height="{IMG_H}" '
            f'loading="eager" fetchpriority="high" decoding="async"></picture>')
    promo = L.get("promo_url") or ("https://iraq.fabletour.com/" + ("" if c == "ar" else L["slug"] + "/"))
    rep = {
        "{{HEAD_SEO}}": head_seo(L, langs),
        "{{FONTS}}": f'<link href="https://fonts.googleapis.com/css2?{fonts}&display=swap" rel="stylesheet">',
        "{{EXTRA_CSS}}": extra_css(L),
        "{{LANGSWITCH}}": lang_switch(L, langs),
        "{{HERO_IMG}}": hero,
        "{{VIDEO}}": video(L),
        "{{FAQ}}": faq(L),
        "{{MORE_TOURS}}": more_tours(L),
        "{{PROMO_HREF}}": promo,
        "{{PROMO_DOMAIN}}": promo.replace("https://", "").rstrip("/"),
        "{{T_JS}}": t_js(L),
        "{{EXTRA_JS}}": EXTRA_JS,
        "{{LANG}}": c,
        "{{DIR}}": L["dir"],
    }
    for k, v in rep.items():
        s = s.replace(k, v)
    t = L["t"]
    missing = []
    def tv(m):
        k = m.group(1)
        if k not in t: missing.append(k); return ""
        return E(t[k])
    def th(m):
        k = m.group(1)
        if k not in t: missing.append(k); return ""
        return t[k]
    s = re.sub(r"\{\{t:([^}]+)\}\}", tv, s)
    s = re.sub(r"\{\{h:([^}]+)\}\}", th, s)
    assert not missing, (c, missing)
    assert "{{" not in s, (c, re.findall(r"\{\{[^}]*\}\}", s)[:5])
    return s


def sitemap(langs):
    path = os.path.join(ROOT, "sitemap.xml")
    sm = open(path, encoding="utf-8").read()
    alts = "\n".join(f'    <xhtml:link rel="alternate" hreflang="{c}" href="{url_of(langs[c])}"/>' for c in ORDER)
    alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url_of(langs[X_DEFAULT])}"/>'
    blocks = []
    for c in ORDER:
        blocks.append(f'''  <url>
    <loc>{url_of(langs[c])}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{"0.9" if c == "ar" else "0.8"}</priority>
{alts}
    <image:image><image:loc>{IMG_JPG}</image:loc></image:image>
  </url>''')
    new = "  <!-- BABYLON-DAY-TRIP:START (generated by _babylon-src/build.py) -->\n" + "\n\n".join(blocks) + \
          "\n  <!-- BABYLON-DAY-TRIP:END -->"
    if "BABYLON-DAY-TRIP:START" in sm:
        sm = re.sub(r"  <!-- BABYLON-DAY-TRIP:START.*?BABYLON-DAY-TRIP:END -->", lambda m: new, sm, flags=re.S)
    else:
        sm, n = re.subn(r"  <url>\s*<loc>https://discovery\.fabletour\.com/babylon-tour\.html</loc>.*?</url>",
                        lambda m: new, sm, count=1, flags=re.S)
        assert n == 1, "babylon block not found in sitemap"
    if "xmlns:image=" not in sm:
        sm = sm.replace('xmlns:xhtml="http://www.w3.org/1999/xhtml"',
                        'xmlns:xhtml="http://www.w3.org/1999/xhtml"\n        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"', 1)
    open(path, "w", encoding="utf-8").write(sm)


def main():
    langs = load()
    tpl = open(os.path.join(SRC, "template.html"), encoding="utf-8").read()
    for c in ORDER:
        L = langs[c]
        out = render(L, langs, tpl)
        if c == "ar":
            p = os.path.join(ROOT, "babylon-tour.html")
        else:
            d = os.path.join(ROOT, "babylon-day-trip", L["slug"])
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "index.html")
        open(p, "w", encoding="utf-8").write(out)
        print(f"{c:8} → {os.path.relpath(p, ROOT)}  ({len(out)//1024} KB)")
    sitemap(langs)
    print("sitemap.xml updated")


if __name__ == "__main__":
    main()
