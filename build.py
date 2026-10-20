#!/usr/bin/env python3
"""Build the static portfolio into site/ from src/content.json.  Usage: python build.py"""
import html
import json
import shutil
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "src", ROOT / "site"
WIDTHS = (600, 1600)
C = json.loads((SRC / "content.json").read_text("utf-8"))
SITE, PRO = C["site"], C["profile"]
BASE = SITE["base_url"].rstrip("/")
PROJECTS = C["projects"]
e = html.escape


def _open(src):
    return ImageOps.exif_transpose(Image.open(ROOT / src)).convert("RGB")


def _save(im, dest, src):
    """Save without EXIF/GPS metadata; skip if dest is newer than src."""
    if dest.exists() and dest.stat().st_mtime >= (ROOT / src).stat().st_mtime:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.suffix == ".webp":
        im.save(dest, "WEBP", quality=80, method=6)
    else:
        im.save(dest, "JPEG", quality=82, optimize=True, progressive=True)


def og_image(src, dest):
    """1200 x 630 link-preview image: the source image fitted on white."""
    im = _open(src)
    im.thumbnail((1100, 560))
    canvas = Image.new("RGB", (1200, 630), "white")
    canvas.paste(im, ((1200 - im.width) // 2, (630 - im.height) // 2))
    _save(canvas, dest, src)


def _font(size, bold=False):
    """Segoe UI on Windows, DejaVu Sans on Linux (GitHub Actions), else Pillow's built-in font."""
    names = ("segoeuib.ttf", "DejaVuSans-Bold.ttf") if bold else ("segoeui.ttf", "DejaVuSans.ttf")
    for name in names + tuple(f"/usr/share/fonts/truetype/dejavu/{n}" for n in names[1:]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def og_title_card(title, dest):
    """1200 x 630 link-preview card with the page title, for pages without images."""
    canvas = Image.new("RGB", (1200, 630), "#1d4ed8")
    d = ImageDraw.Draw(canvas)
    big = _font(64, bold=True)
    small = _font(34)
    lines, line = [], ""
    for word in title.split():
        if line and d.textlength(f"{line} {word}", font=big) > 1040:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    lines.append(line)
    y = 315 - len(lines) * 42
    for text in lines:
        d.text((80, y), text, font=big, fill="white")
        y += 84
    d.text((80, y + 24), SITE["title"], font=small, fill="#dbeafe")
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest, "JPEG", quality=88)


def resize(src):
    """Write web sizes of an image; return {"w", "h", "files": {width: stem}} with stems relative to site/."""
    src_p = ROOT / src
    stem = f"assets/img/{src_p.parent.name}/{src_p.stem}"
    with Image.open(src_p) as raw:
        w, h = ImageOps.exif_transpose(raw).size
    full = None
    files = {}
    for target in WIDTHS:
        tw = min(target, w)
        files[tw] = f"{stem}-{tw}"
        for ext in ("webp", "jpg"):
            dest = OUT / f"{stem}-{tw}.{ext}"
            if dest.exists() and dest.stat().st_mtime >= src_p.stat().st_mtime:
                continue
            full = full or _open(src)
            _save(full.resize((tw, round(h * tw / w)), Image.LANCZOS), dest, src)
    return {"w": w, "h": h, "files": files}


def picture(src, alt, root, sizes, lazy=True):
    r = resize(src)
    srcset = lambda ext: ", ".join(f"{root}{s}.{ext} {w}w" for w, s in r["files"].items())
    big = root + r["files"][max(r["files"])]
    load = ' loading="lazy"' if lazy else ' fetchpriority="high"'
    return (f'<picture><source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
            f'<img src="{big}.jpg" srcset="{srcset("jpg")}" sizes="{sizes}" width="{r["w"]}" height="{r["h"]}"'
            f' alt="{e(alt)}"{load} decoding="async"></picture>'), big


def figure(im, root, sizes):
    pic, big = picture(im["src"], im["alt"], root, sizes)
    cap = im.get("caption", "")
    return (f'<figure class="shot"><a class="lb" href="{big}.jpg" data-caption="{e(cap or im["alt"])}">{pic}'
            f'<span class="sr-only">Open larger image</span></a>'
            + (f"<figcaption>{e(cap)}</figcaption>" if cap else "") + "</figure>")


def video(v, root):
    r = resize(v["poster"])
    poster = root + r["files"][max(r["files"])] + ".jpg"
    name = Path(v["src"]).name
    shutil.copy2(ROOT / v["src"], OUT / "assets/video" / name)
    return (f'<figure class="clip{" tall" if r["h"] > r["w"] else ""}"><video controls preload="none" playsinline poster="{poster}" '
            f'width="{r["w"]}" height="{r["h"]}" aria-label="{e(v["title"])}"><source src="{root}assets/video/{name}" type="video/mp4">'
            f'<a href="{root}assets/video/{name}">Download the video</a></video><figcaption>{e(v["title"])}</figcaption></figure>')


def items(lst):
    out = []
    for it in lst:
        if isinstance(it, str):
            out.append(f"<li>{e(it)}</li>")
        else:
            out.append(f"<li>{e(it['text'])}{items(it['items'])}</li>")
    return "<ul>" + "".join(out) + "</ul>"


def page(path, title, desc, body, root, head_extra="", og="assets/img/og.jpg"):
    url = f"{BASE}/{path}".removesuffix("index.html")
    nav = "".join(f'<li><a href="{root}index.html#{a}">{l}</a></li>' for a, l in
                  [("projects", "Projects"), ("experience", "Experience"), ("about", "About"), ("contact", "Contact")])
    html_ = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['title'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{BASE}/{og}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/style.css">
<script src="{root}assets/script.js" defer></script>{head_extra}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap bar">
<a class="brand" href="{root}index.html"><span class="mono" aria-hidden="true">RK</span>{e(PRO['name'])}</a>
<button class="nav-toggle" aria-expanded="false" aria-controls="nav">Menu</button>
<nav id="nav" aria-label="Main"><ul>{nav}<li><a class="btn small" href="{root}{SITE['resume_pdf']}">Resume</a></li></ul></nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="site-footer"><div class="wrap">
<p><a href="mailto:{PRO['email']}">{PRO['email']}</a> · <a href="tel:+1{PRO['phone'].replace('.', '')}">{PRO['phone']}</a> · <a href="{PRO['linkedin']}">LinkedIn</a> · {e(PRO['location'])}</p>
<p>© {date.today().year} {e(PRO['name'])}</p>
</div></footer>
</body>
</html>
"""
    dest = OUT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html_, "utf-8")


def card(p, root):
    href = f"{root}projects/{p['slug']}.html"
    show = p["images"] and p.get("card_image", True)
    if show:
        media, _ = picture(p["images"][0]["src"], "", root, "(min-width: 900px) 33vw, 100vw")
    else:
        media = f'<div class="stat" aria-hidden="true">{e(p.get("stat", p["title"]))}</div>'
    return (f'<article class="card"><div class="card-media{"" if show else " text"}">{media}</div><div class="card-body">'
            f'<p class="kicker">{e(p["kind"])}</p><h3><a href="{href}">{e(p["title"])}</a></h3>'
            f'<p>{e(p["card"])}</p></div></article>')


def home():
    root = ""
    feat = "".join(card(p, root) for p in PROJECTS if p["home"] == "featured")
    other = "".join(f'<li><a href="projects/{p["slug"]}.html">{e(p["title"])}</a> <span>{e(p["card"])}</span></li>'
                    for p in PROJECTS if p["home"] == "other")
    titles = {p["slug"]: p["title"] for p in PROJECTS}
    gal = C.get("cad_gallery")
    cad = ""
    if gal:
        for g in gal["items"]:
            pic, big = picture(g["image"]["src"], g["image"]["alt"], root, "(min-width: 900px) 200px, 50vw")
            title = f'<a href="projects/{g["link"]}.html">{e(g["title"])}</a>' if g.get("link") else e(g["title"])
            purpose = f'<p>{e(g["purpose"])}</p>' if g.get("purpose") else ""
            cad += (f'<li><a class="lb" href="{big}.jpg" data-caption="{e(g["title"])}: {e(g["size"])}">{pic}'
                    f'<span class="sr-only">Open larger image</span></a><h4>{title}</h4>'
                    f'<p class="muted">{e(g["size"])}</p>{purpose}<p>{e(g["notes"])}</p></li>')
        cad = f'<h3 class="sub">{e(gal["heading"])}</h3><ul class="cad">{cad}</ul>'

    exp = ""
    for j in C["experience"]:
        group = f' <span class="muted">({e(j["group"])})</span>' if j.get("group") else ""
        rel = ""
        if j.get("projects"):
            rel = '<p class="related">Case studies: ' + " · ".join(
                f'<a href="projects/{s}.html">{e(titles[s])}</a>' for s in j["projects"]) + "</p>"
        exp += (f'<li class="job"><div class="job-head"><h3>{e(j["title"])} · {e(j["org"])}{group}</h3>'
                f'<p class="muted">{e(j["date"])} · {e(j["location"])}</p></div>{items(j["bullets"])}{rel}</li>')
    ed = C["education"]
    capstone = "".join(f'<p>Senior capstone: <a href="projects/{p["slug"]}.html">{e(p["title"])}</a></p>'
                       for p in PROJECTS if p["home"] == "education")
    skills = "".join(f'<div><h3>{e(s["label"])}</h3><p>{" · ".join(e(i) for i in s["items"])}</p></div>' for s in C["skills"])
    chips = "".join(f"<li>{e(h)}</li>" for h in C["highlights"])
    hob = "".join(f'<figure>{picture(h["src"], h["alt"], root, "160px")[0]}<figcaption>{e(h["caption"])}</figcaption></figure>'
                  for h in PRO["hobbies"])
    head_pic, _ = picture(PRO["headshot"]["src"], PRO["headshot"]["alt"], root, "(min-width: 900px) 360px, 70vw", lazy=False)
    citizenship = f'<li><span>Citizenship</span>{e(PRO["citizenship"])}</li>' if PRO.get("citizenship") else ""
    ld = {"@context": "https://schema.org", "@type": "Person", "name": PRO["name"], "jobTitle": PRO["headline"],
          "email": "mailto:" + PRO["email"], "url": BASE + "/", "sameAs": [PRO["linkedin"]],
          "alumniOf": ed["school"], "address": {"@type": "PostalAddress", "addressLocality": "Boston", "addressRegion": "MA"}}
    body = f"""<section class="hero"><div class="wrap hero-grid">
<div><h1>{e(PRO['name'])}</h1><p class="role">{e(PRO['headline'])}</p><p class="pitch">{e(PRO['pitch'])}</p>
<p class="tagline">{e(PRO['tagline'])}</p>
<p class="actions"><a class="btn" href="{SITE['resume_pdf']}">Resume (PDF)</a><a class="btn ghost" href="{PRO['linkedin']}">LinkedIn</a><a class="btn ghost" href="mailto:{PRO['email']}">Email</a></p></div>
<div class="headshot">{head_pic}</div></div>
<div class="wrap"><ul class="chips" aria-label="Skills and honors">{chips}</ul></div></section>
<section id="projects" class="wrap"><h2>Projects</h2><div class="grid">{feat}</div>
<h3 class="sub">Other builds</h3><ul class="other">{other}</ul>{cad}</section>
<section id="experience" class="wrap"><h2>Experience</h2><ol class="jobs">{exp}</ol></section>
<section id="skills" class="wrap"><h2>Education &amp; skills</h2><div class="skills">
<div><h3>{e(ed['school'])}</h3><p>{e(ed['degree'])}, {e(ed['date'])}<br>{e(ed['location'])}</p>
<p class="muted">Courses: {e(', '.join(ed['courses']))}</p>{capstone}</div>{skills}</div></section>
<section id="about" class="wrap about"><div><h2>About</h2>{''.join(f'<p>{e(t)}</p>' for t in PRO['about'])}<p>{e(PRO['hobbies_text'])}</p></div>
<div class="hobbies">{hob}</div></section>
<section id="contact" class="wrap contact"><h2>Contact</h2><p>The fastest way to reach me is email.</p>
<ul><li><span>Email</span><a href="mailto:{PRO['email']}">{PRO['email']}</a> <button class="copy" data-copy="{PRO['email']}" type="button">Copy email</button><span class="copied" role="status" aria-live="polite"></span></li>
<li><span>Phone</span><a href="tel:+1{PRO['phone'].replace('.', '')}">{PRO['phone']}</a></li>
<li><span>LinkedIn</span><a href="{PRO['linkedin']}">LinkedIn profile</a></li>
<li><span>Location</span>{e(PRO['location'])}</li>
{citizenship}</ul></section>"""
    page("index.html", SITE["title"], SITE["description"], body, root,
         f'\n<script type="application/ld+json">{json.dumps(ld)}</script>')


def project(i, p):
    root = "../"
    summary = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in p["summary"].items())
    intro = f'<p class="note">{e(p["intro"])}</p>' if p.get("intro") else ""
    figs = [figure(im, root, "(min-width: 900px) 600px, 100vw") for im in p["images"]]
    at = p.get("video_position", 0)
    media = "".join(figs[:at]) + "".join(video(v, root) for v in p["videos"]) + "".join(figs[at:])
    media = f'<section class="gallery" aria-label="Images and videos">{media}</section>' if media else ""
    secs = "".join(f"<section><h2>{e(s['heading'])}</h2>{items(s['items'])}</section>" for s in p["sections"])
    nav = ""
    for rel, j in (("Previous", i - 1), ("Next", i + 1)):
        if 0 <= j < len(PROJECTS):
            q = PROJECTS[j]
            nav += f'<a class="{rel.lower()}" href="{q["slug"]}.html"><span>{rel} project</span>{e(q["title"])}</a>'
    body = f"""<article class="wrap project">
<p class="crumb"><a href="../index.html#projects">← All projects</a></p>
<header><p class="kicker">{e(p['kind'])}</p><h1>{e(p['title'])}</h1></header>
<dl class="summary">{summary}</dl>{intro}{media}<div class="writeup">{secs}</div>
<nav class="pager" aria-label="More projects">{nav}</nav></article>"""
    desc = f"{p['title']}: {p['card']} A project by {PRO['name']}, mechanical engineer."
    og = f"assets/img/og/{p['slug']}.jpg"
    og_src = p.get("og_image") or (p["images"][0]["src"] if p["images"] else None)
    if og_src:
        og_image(og_src, OUT / og)
    else:
        og_title_card(p["title"], OUT / og)
    page(f"projects/{p['slug']}.html", f"{p['title']} | {SITE['title']}", desc, body, root, og=og)


def extras():
    body = """<section class="wrap notfound"><h1>Page not found</h1><p>That page does not exist or has moved.</p>
<p><a class="btn" href="/">Go to the home page</a></p></section>"""
    page("404.html", f"Page not found | {SITE['title']}", SITE["description"], body, "/")
    urls = [""] + [f"projects/{p['slug']}.html" for p in PROJECTS]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"<url><loc>{BASE}/{u}</loc></url>\n" for u in urls) + "</urlset>\n", "utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", "utf-8")
    (OUT / ".nojekyll").write_text("", "utf-8")
    og_image(SITE["og_image"], OUT / "assets/img/og.jpg")


def main():
    for d in ("assets/video", "projects"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    for f in (SRC / "assets").iterdir():
        shutil.copy2(f, OUT / "assets" / f.name)
    shutil.copy2(SRC / "favicon.svg", OUT / "favicon.svg")
    shutil.copy2(ROOT / SITE["resume_pdf"], OUT / SITE["resume_pdf"])
    home()
    for i, p in enumerate(PROJECTS):
        project(i, p)
    extras()
    print(f"Built {len(PROJECTS) + 2} pages into {OUT}")


if __name__ == "__main__":
    main()
