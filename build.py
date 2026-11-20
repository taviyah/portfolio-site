"""Builds the portfolio site into dist/.

    python build.py

Content lives in content/*.json (Hebrew and English side by side), styles in assets/style.css,
screenshots in assets/media/<project-slug>/. No packages needed beyond Python 3.
"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
LANGS = ("he", "en")

SITE = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
PROJECTS = json.loads((ROOT / "content/projects.json").read_text(encoding="utf-8"))
NOTES = json.loads((ROOT / "content/notes.json").read_text(encoding="utf-8"))
CONTACT = SITE["contact"]
IS_DRAFT = not (CONTACT.get("email") or CONTACT.get("whatsapp"))
# Browsers keep /assets/* for a week (_headers), so the stylesheet link carries a version that
# changes whenever the file does; otherwise returning visitors would see old styles.
import hashlib
CSS_VERSION = hashlib.sha256((ROOT / "assets/style.css").read_bytes()).hexdigest()[:10]

# Simple line icons, drawn on a 24x24 grid, used when a project has no app icon image.
ICONS = {
    "journal": '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/><path d="M9 8h6M9 11h4"/>',
    "read": '<path d="M4 5h9M4 9h12M4 13h7"/><path d="M15 15c1.2-1 1.2-3 0-4M18 17.5c2.6-2.4 2.6-6.6 0-9"/>',
    "silence": '<path d="M6 16V11a6 6 0 0 1 9.5-4.9M18 11v5l1.5 2H6"/><path d="M10 21h4M3 3l18 18"/>',
    "wave": '<path d="M3 12h2l2-6 3 12 3-15 3 15 2-6h3"/>',
    "sun": '<circle cx="12" cy="13" r="3.5"/><path d="M2 20c3-9 17-9 20 0"/><path d="M12 4v2M5.5 6.5l1.4 1.4M18.5 6.5l-1.4 1.4"/>',
    "cloud": '<path d="M7 17a4 4 0 1 1 .8-7.9A5.5 5.5 0 0 1 18.5 11 3 3 0 0 1 18 17z"/><path d="M9 20l-1 2M13 20l-1 2M17 20l-1 2"/>',
    "drop": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/><path d="M9.5 14.5a2.5 2.5 0 0 0 2.5 2.5"/>',
    "voice": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/>',
    "transcribe": '<path d="M4 8v8M7.5 5v14M11 9v6"/><path d="M14 8h6M14 12h6M14 16h4"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    "notes": '<path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/>',
    "bars": '<path d="M3 20h3v-4H3zM8 20h3v-8H8zM13 20h3V8h-3zM18 20h3V4h-3z"/>',
    "signal": '<path d="M4 20h2v-4H4zM9 20h2v-8H9zM14 20h2V8h-2z"/><path d="M18 4l4 4M22 4l-4 4"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "chat": '<path d="M4 20l1.5-4A8 8 0 1 1 9 19.5z"/>',
    "code": '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5"/>',
    "person": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "doc": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
}


def svg(name, size=24, cls="ico"):
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{ICONS[name]}</svg>')


def e(s):
    return html.escape(str(s), quote=True)


def t(value, lang):
    """Pick the language from a {"he":..., "en":...} value."""
    return value[lang] if isinstance(value, dict) else value


def prefix(lang):
    return "" if lang == "he" else "/en"


def app_icon(slug):
    for ext in ("png", "svg"):
        p = ROOT / "assets/media" / slug / f"icon.{ext}"
        if p.exists():
            return f"/assets/media/{slug}/icon.{ext}"
    return None


def visual(item, lang, big=False):
    """The coloured panel at the top of a card: wide media if any, else the app icon, else a line icon."""
    media = [m for m in item.get("media", []) if m.get("wide")]
    if media:
        m = media[0]
        return (f'<div class="visual has-media" style="--accent:{item["accent"]}">'
                f'<img src="/assets/media/{e(m["file"])}" alt="{e(t(m["alt"], lang))}" loading="lazy"'
                + (' style="object-fit:cover;object-position:top"' if m.get("fit") == "cover" else "") + '></div>')
    icon = app_icon(item["slug"])
    inner = (f'<img class="appicon" src="{icon}" alt="" width="96" height="96" loading="lazy">' if icon
             else svg(item["icon"], 64 if big else 48, "glyph"))
    return f'<div class="visual" style="--accent:{item["accent"]}">{inner}</div>'


def chips(stack):
    return '<ul class="chips">' + "".join(f"<li>{e(s)}</li>" for s in stack) + "</ul>"


# ---------- page shell ----------

def page(lang, path_he, path_en, title, description, body, body_class=""):
    S = SITE[lang]
    other = "en" if lang == "he" else "he"
    other_path = path_en if lang == "he" else path_he
    name = t(SITE["name"], lang)
    p = prefix(lang)
    draft = f'<div class="draft">{e(S["draft_bar"])}</div>' if IS_DRAFT else ""
    domain = SITE.get("domain", "").rstrip("/")
    canonical = ""
    if domain:
        cur = path_he if lang == "he" else path_en
        canonical = (f'<link rel="canonical" href="{domain}{cur}">'
                     f'<link rel="alternate" hreflang="he" href="{domain}{path_he}">'
                     f'<link rel="alternate" hreflang="en" href="{domain}{path_en}">')
    nav = S["nav"]
    return f"""<!doctype html>
<html lang="{lang}" dir="{S['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
{canonical}
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;700&family=Rubik:wght@500;600;700&display=swap">
<link rel="stylesheet" href="/assets/style.css?v={CSS_VERSION}">
</head>
<body class="{body_class}">
{draft}
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="{p}/">{e(name)}<span class="dot"></span></a>
    <nav aria-label="main">
      <a href="{p}/#work">{e(nav['work'])}</a>
      <a href="{p}/#services">{e(nav['services'])}</a>
      <a href="{p}/#about">{e(nav['about'])}</a>
      <a class="nav-cta" href="{p}/#contact">{e(nav['contact'])}</a>
      <a class="lang" href="{other_path}" hreflang="{other}" lang="{other}">{e(S['lang_switch'])}</a>
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <span>© 2026 {e(name)}</span>
    <span>{e(S['footer'])}</span>
  </div>
</footer>
</body>
</html>
"""


def contact_buttons(lang):
    S = SITE[lang]
    out = []
    if CONTACT.get("whatsapp"):
        digits = re.sub(r"\D", "", CONTACT["whatsapp"])
        out.append(f'<a class="btn primary" href="https://wa.me/{digits}">{svg("chat")}WhatsApp</a>')
    if CONTACT.get("email"):
        out.append(f'<a class="btn" href="mailto:{e(CONTACT["email"])}">{svg("mail")}{e(CONTACT["email"])}</a>')
    if CONTACT.get("github"):
        out.append(f'<a class="btn" href="{e(CONTACT["github"])}">{svg("code")}GitHub</a>')
    if CONTACT.get("linkedin"):
        out.append(f'<a class="btn" href="{e(CONTACT["linkedin"])}">{svg("person")}LinkedIn</a>')
    if CONTACT.get("cv_pdf"):
        label = "קורות חיים" if lang == "he" else "CV"
        out.append(f'<a class="btn" href="{e(CONTACT["cv_pdf"])}">{svg("doc")}{label}</a>')
    if not out:
        return f'<p class="missing">{e(S["contact_missing"])}</p>'
    return '<div class="btns">' + "".join(out) + "</div>"


# ---------- home ----------

def featured_card(pr, lang, lead=False):
    S = SITE[lang]
    L = S["labels"]
    p = prefix(lang)
    href = f"{p}/work/{pr['slug']}/"
    demo = ""
    for ln in pr.get("links", []):
        if ln.get("primary"):
            demo = f'<a class="btn primary small" href="{e(ln["url"])}">{e(t(ln["label"], lang))}</a>'
    kind = pr.get("kind", "own")
    return f"""<article class="card feat{' lead' if lead else ''}">
  <a class="cover" href="{href}" tabindex="-1" aria-hidden="true">{visual(pr, lang, big=lead)}</a>
  <div class="card-body">
    <div class="meta"><span class="badge {kind}">{e(L[kind])}</span><span class="status">{e(t(pr['status'], lang))}</span></div>
    <h3><a href="{href}">{e(t(pr['title'], lang))}</a></h3>
    <p>{e(t(pr['tagline'], lang))}</p>
    <div class="card-foot">
      <a class="more" href="{href}">{e(S['case_study'])} {svg('arrow', 18)}</a>
      {demo}
    </div>
  </div>
</article>"""


def small_card(pr, lang):
    S = SITE[lang]
    url = pr.get("url")
    link = (f'<a class="more" href="{e(url)}" rel="noopener">{e(S["labels"]["original"])} {svg("arrow", 16)}</a>'
            if url else "")
    if pr.get("link"):
        ln = pr["link"]
        href = prefix(lang) + ln["url"] if ln["url"].startswith("/") else ln["url"]
        link = f'<a class="more" href="{e(href)}">{e(t(ln["label"], lang))} {svg("arrow", 16)}</a>'
    if pr.get("source"):
        label = "קוד המקור ב־GitHub" if lang == "he" else "Source code on GitHub"
        link += f'<a class="more" href="{e(pr["source"])}" rel="noopener">{label} {svg("arrow", 16)}</a>'

    icon = app_icon(pr["slug"])
    mark = (f'<img src="{icon}" alt="" width="40" height="40">' if icon else svg(pr["icon"], 22))
    return f"""<article class="mini" style="--accent:{pr['accent']}">
  <div class="mini-ico">{mark}</div>
  <h3>{e(t(pr['title'], lang))}</h3>
  <p>{e(t(pr['tagline'], lang))}</p>
  {chips(pr.get('stack', []))}
  {link}
</article>"""


def home(lang):
    S = SITE[lang]
    p = prefix(lang)
    feats = [x for x in PROJECTS if x.get("featured")]
    rest = [x for x in PROJECTS if not x.get("featured")]
    stats = "".join(f'<div class="stat"><b>{e(s["n"])}</b><span>{e(s["t"])}</span></div>' for s in S["stats"])
    feat_html = "".join(featured_card(x, lang, lead=(i == 0)) for i, x in enumerate(feats))
    rest_html = "".join(small_card(x, lang) for x in rest)
    notes_html = "".join(
        f"""<a class="note-card" href="{p}/notes/{n['slug']}/" style="--accent:{n['accent']}">
  <span class="note-ico">{svg(n['icon'], 28)}</span>
  <span class="note-txt"><small>{e(S['note_title'])}</small><b>{e(t(n['title'], lang))}</b><span>{e(t(n['tagline'], lang))}</span></span>
  <span class="note-go">{e(S['read_more'])} {svg('arrow', 18)}</span>
</a>""" for n in NOTES)
    services = "".join(f'<div class="svc"><h3>{e(s["t"])}</h3><p>{e(s["d"])}</p></div>' for s in S["services_list"])
    process = "".join(f'<li><b>{e(s["t"])}</b><span>{e(s["d"])}</span></li>' for s in S["process"])
    about = "".join(f"<p>{e(x)}</p>" for x in S["about_body"])
    body = f"""
<section class="hero">
  <div class="wrap">
    <p class="kicker">{e(S['hero_kicker'])}</p>
    <h1>{e(S['hero_title'])}</h1>
    <p class="lede">{e(S['hero_body'])}</p>
    <div class="btns">
      <a class="btn primary" href="#contact">{e(S['hero_cta'])}</a>
      <a class="btn" href="#work">{e(S['hero_cta2'])}</a>
    </div>
    <div class="stats">{stats}</div>
  </div>
</section>

<section id="work" class="sec">
  <div class="wrap">
    <h2 class="sec-title">{e(S['featured_title'])}</h2>
    <div class="feat-grid">{feat_html}</div>
    {notes_html}
    <h2 class="sec-title sub">{e(S['more_title'])}</h2>
    <div class="mini-grid">{rest_html}</div>
  </div>
</section>

<section id="services" class="sec tint">
  <div class="wrap">
    <h2 class="sec-title">{e(S['services_title'])}</h2>
    <p class="sec-lede">{e(S['services_body'])}</p>
    <div class="svc-grid">{services}</div>
    <h3 class="process-title">{e(S['process_title'])}</h3>
    <ol class="process">{process}</ol>
  </div>
</section>

<section id="about" class="sec">
  <div class="wrap about">
    <div class="about-side">
      <h2 class="sec-title">{e(S['about_title'])}</h2>
      <img class="portrait" src="/assets/media/me/portrait.webp" width="600" height="750" alt="{e(t(SITE['name'], lang))}" loading="lazy" decoding="async">
    </div>
    <div class="about-txt">{about}
      <p class="facts"><b>{e(S['about_langs_label'])}:</b> {e(S['about_langs'])}</p>
    </div>
  </div>
</section>

<section id="contact" class="sec contact">
  <div class="wrap">
    <div class="contact-head">
      <img class="avatar" src="/assets/media/me/avatar.webp" width="240" height="240" alt="" loading="lazy" decoding="async">
      <h2 class="sec-title">{e(S['contact_title'])}</h2>
    </div>
    <p class="sec-lede">{e(S['contact_body'])}</p>
    {contact_buttons(lang)}
  </div>
</section>
"""
    name = t(SITE["name"], lang)
    return page(lang, "/", "/en/", f"{name} · {S['hero_kicker']}", S["hero_body"], body, "home")


# ---------- project page ----------

def project_page(pr, lang):
    S = SITE[lang]
    L = S["labels"]
    p = prefix(lang)
    feats = [x for x in PROJECTS if x.get("featured")]
    i = feats.index(pr)
    nxt = feats[(i + 1) % len(feats)]
    links = "".join(
        f'<a class="btn{" primary" if ln.get("primary") else ""}" href="{e(ln["url"])}">{e(t(ln["label"], lang))}</a>'
        for ln in pr.get("links", []))
    media = pr.get("media", [])
    if media:
        shots = "".join(
            f'<figure class="{"wide" if m.get("wide") else "phone"}"><img src="/assets/media/{e(m["file"])}" '
            f'alt="{e(t(m["alt"], lang))}" loading="lazy"></figure>' for m in media)
        gallery = f'<div class="gallery">{shots}</div>'
    else:
        gallery = f'<div class="gallery empty">{visual(pr, lang, big=True)}<p>{e(L["screens_soon"])}</p></div>'
    built = "".join(f"<li>{e(x)}</li>" for x in t(pr["built"], lang))
    hard = "".join(f"<li>{x}</li>" for x in t(pr["hard"], lang))  # contains <strong>, written by us
    note = (f'<aside class="callout"><b>{e(L["note"])}:</b> {e(t(pr["note"], lang))}</aside>'
            if pr.get("note") else "")
    kind = pr.get("kind", "own")
    intro = f'<p class="intro">{e(t(pr["intro"], lang))}</p>' if pr.get("intro") else ""
    body = f"""
<article class="proj" style="--accent:{pr['accent']}">
  <div class="wrap">
    <a class="back" href="{p}/#work">{e(L['back'])}</a>
    <header class="proj-head">
      <div>
        <span class="badge {kind}">{e(L[kind])}</span>
        <h1>{e(t(pr['title'], lang))}</h1>
        <p class="lede">{e(t(pr['tagline'], lang))}</p>
        <div class="btns">{links}</div>
      </div>
      <dl class="facts-box">
        <div><dt>{e(L['status'])}</dt><dd>{e(t(pr['status'], lang))}</dd></div>
        <div><dt>{e(L['platforms'])}</dt><dd>{e(t(pr['platforms'], lang))}</dd></div>
        <div><dt>{e(L['year'])}</dt><dd>{e(pr['year'])}</dd></div>
      </dl>
    </header>
    {intro}
    {gallery}
    <div class="proj-body">
      <section><h2>{e(L['problem'])}</h2><p>{e(t(pr['problem'], lang))}</p></section>
      <section><h2>{e(L['built'])}</h2><ul class="ticks">{built}</ul></section>
      <section><h2>{e(L['hard'])}</h2><ul class="hard">{hard}</ul>{note}</section>
      <section><h2>{e(L['stack'])}</h2>{chips(pr['stack'])}</section>
    </div>
    <a class="next" href="{p}/work/{nxt['slug']}/" style="--accent:{nxt['accent']}">
      <small>{'הבא' if lang == 'he' else 'Next'}</small>
      <b>{e(t(nxt['title'], lang))}</b> {svg('arrow', 22)}
    </a>
  </div>
</article>"""
    title = f"{t(pr['title'], lang)} · {t(SITE['name'], lang)}"
    return page(lang, f"/work/{pr['slug']}/", f"/en/work/{pr['slug']}/", title, t(pr["tagline"], lang), body)


def note_page(n, lang):
    S = SITE[lang]
    p = prefix(lang)
    body = f"""
<article class="note" style="--accent:{n['accent']}">
  <div class="wrap narrow">
    <a class="back" href="{p}/#work">{e(S['labels']['back'])}</a>
    <p class="kicker">{e(S['note_title'])}</p>
    <h1>{e(t(n['title'], lang))}</h1>
    <p class="lede">{e(t(n['tagline'], lang))}</p>
    <div class="prose">{''.join(t(n['body'], lang))}</div>
  </div>
</article>"""
    title = f"{t(n['title'], lang)} · {t(SITE['name'], lang)}"
    return page(lang, f"/notes/{n['slug']}/", f"/en/notes/{n['slug']}/", title, t(n["tagline"], lang), body)


# ---------- demo ----------

def build_demo():
    src = (ROOT / "demo/lesson-journal/app-source.html").read_text(encoding="utf-8")
    S = SITE["he"]
    banner = (f'<div id="demo-bar" dir="rtl" style="position:fixed;inset-inline:0;bottom:0;z-index:50;display:flex;'
              f'gap:12px;align-items:center;justify-content:center;flex-wrap:wrap;padding:10px 16px;background:#1D2129;'
              f'color:#fff;font:14px/1.4 Heebo,system-ui,sans-serif">'
              f'<span>{e(S["demo_banner"])}</span>'
              f'<a href="/work/lesson-journal/" style="color:#C9B8F0">{e(S["demo_back"])}</a></div>')
    out = src.replace("<head>", '<head>\n<script src="fake-backend.js"></script>', 1)
    out = out.replace('<base target="_top">', "", 1)
    out = out.replace("<body>", "<body>\n" + banner, 1)
    out = out.replace("<title>", "<title>דמו · ", 1) if "<title>" in out else out.replace(
        "</head>", "<title>יומן שיעורים · דמו</title>\n</head>", 1)
    d = DIST / "demo/lesson-journal"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(out, encoding="utf-8")
    shutil.copy(ROOT / "demo/lesson-journal/fake-backend.js", d / "fake-backend.js")


# ---------- write everything ----------

def write(path, text):
    f = DIST / path.lstrip("/") / "index.html" if not path.endswith(".html") else DIST / path.lstrip("/")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "assets", DIST / "assets")
    for f in ("_headers", "robots.txt"):
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, DIST / f)
    for lang in LANGS:
        p = prefix(lang)
        write(f"{p}/", home(lang))
        for pr in PROJECTS:
            if pr.get("featured"):
                write(f"{p}/work/{pr['slug']}/", project_page(pr, lang))
        for n in NOTES:
            write(f"{p}/notes/{n['slug']}/", note_page(n, lang))
    build_demo()
    four = page("he", "/", "/en/", "404", "", '<section class="hero"><div class="wrap"><p class="kicker">404</p>'
                '<h1>הדף לא נמצא · Page not found</h1><div class="btns"><a class="btn primary" href="/">עמוד הבית</a>'
                '<a class="btn" href="/en/">Home (English)</a></div></div></section>')
    (DIST / "404.html").write_text(four, encoding="utf-8")
    pages = sorted(str(x.relative_to(DIST)) for x in DIST.rglob("*.html"))
    print(f"Built {len(pages)} pages into {DIST}" + ("  (DRAFT: contact details missing)" if IS_DRAFT else ""))


if __name__ == "__main__":
    main()
