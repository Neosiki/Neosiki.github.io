#!/usr/bin/env python3
"""문명 연작 정적 페이지 빌더 (한국어 / English).

사용법:  python3 tools/fiction/build_fiction.py
입력  :  tools/fiction/series.json  +  fiction/_manuscripts/*.md  +  assets/fiction/<slug>/*.jpg
출력  :  fiction.html · fiction/<slug>.html          (한국어)
         en/fiction.html · en/fiction/<slug>.html    (English)
         두 언어는 <link rel="alternate" hreflang>으로 상호 연결된다.

새 편 추가는 tools/fiction/README.md 참고.
"""
import json, os, re, glob, html, sys, io

ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CFG   = os.path.join(ROOT, "tools", "fiction", "series.json")
MSRC  = os.path.join(ROOT, "fiction", "_manuscripts")
ASSET = os.path.join(ROOT, "assets", "fiction")

try:
    import markdown as mdlib
except ImportError:
    sys.exit("markdown 패키지가 필요합니다:  pip install markdown")

# ─────────────────────────── 언어별 문구 ───────────────────────────
T = {
  "ko": {
    "brand": "윤영식 · NextAI", "kind": "단편소설 · 영상",
    "nav": [("index.html", "프로젝트"), ("about.html", "소개·커리어")],
    "hubNav": "문명 연작", "switch": "EN", "switchTitle": "English",
    "synopsis": "SYNOPSIS", "repo": "저장소", "tech": "기술 구성",
    "stills": "스틸", "scenes": "장면 기준 이미지 %d장",
    "index": "← 연작 목록", "nextSoon": "다음 편 준비 중",
    "watch": "영상 보기", "otherLang": "English version", "blog": "네이버 블로그에서 보기",
    "pending": "링크 준비 중", "home": "프로젝트 홈",
    "eyebrow": "SHORT FICTION &amp; FILM · %d PARTS",
    "progress": "/ %d편 공개", "soon": "제%d편 — 제%d편<br />순차 공개 예정",
    "noText": ("한국어 전문 준비 중",
               "이 편은 영상과 스틸을 먼저 공개했습니다. 한국어 원고를 게시 형식으로 정리해 이어서 올립니다."),
  },
  "en": {
    "brand": "YoungShig Yoon · NextAI", "kind": "Short fiction · Film",
    "nav": [], "hubNav": "The Civilization Cycle", "switch": "한국어", "switchTitle": "한국어판",
    "synopsis": "SYNOPSIS", "repo": "Source", "tech": "Production",
    "stills": "Stills", "scenes": "%d scene reference images",
    "index": "← All parts", "nextSoon": "Next part in production",
    "watch": "Watch the film", "otherLang": "한국어판", "blog": "Read on Naver blog",
    "pending": "link coming", "home": "Project home",
    "eyebrow": "SHORT FICTION &amp; FILM · %d PARTS",
    "progress": "/ %d parts published", "soon": "Parts %d — %d<br />published in sequence",
    "noText": ("Full text coming",
               "The film and stills are published first. The full text follows once prepared for the web."),
  },
}

def val(w, lang, key, default=None):
    """영문 페이지면 w['en'][key]를 우선 사용하고 없으면 공통값으로 되돌아간다."""
    if lang == "en" and isinstance(w.get("en"), dict) and key in w["en"]:
        return w["en"][key]
    return w.get(key, default)

# ─────────────────────────── 템플릿 ───────────────────────────
BASE_CSS = """
:root{
  --paper:#ffffff; --paper-2:#f7faf9; --ink:#1f2d40; --muted:#687584;
  --line:rgba(31,45,64,.15); --teal:#6f9995; --teal-dark:#416f6b;
  --lime:#edf4dc; --orange:#edb49a; --deep:#16212f;
  --display:"Noto Serif KR","Nanum Myeongjo","Batang",serif;
  --body:"Noto Sans KR","Pretendard","Malgun Gothic",sans-serif;
  --mono:"Bahnschrift","Consolas",monospace;
  --max:1180px; --read:44rem;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);line-height:1.75;-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:inherit}
.wrap{max-width:var(--max);margin:0 auto;padding:0 24px}
.topbar{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.topbar .wrap{display:flex;align-items:center;justify-content:space-between;height:60px;gap:16px}
.brand{font-family:var(--display);font-weight:700;font-size:1.02rem;text-decoration:none;letter-spacing:-.01em}
.topnav{display:flex;align-items:center;gap:20px;font-size:.86rem}
.topnav a{white-space:nowrap}
.topbar .brand{white-space:nowrap}
.topnav a{color:var(--muted);text-decoration:none}
.topnav a:hover,.topnav a[aria-current]{color:var(--teal-dark)}
.langsw{font-family:var(--mono);font-size:.74rem;letter-spacing:.08em;border:1px solid var(--line);
  border-radius:99px;padding:5px 12px;color:var(--teal-dark)!important;text-decoration:none}
.langsw:hover{background:var(--lime)}
.eyebrow{font-family:var(--mono);font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--teal-dark)}
.rule{height:1px;background:var(--line);border:0;margin:0}
footer{border-top:1px solid var(--line);margin-top:72px;padding:32px 0 56px;color:var(--muted);font-size:.82rem}
footer .wrap{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between}
@media (max-width:700px){
  .topbar .wrap{flex-wrap:wrap;height:auto;min-height:0;padding-top:9px;padding-bottom:10px;row-gap:7px;column-gap:0}
  .topbar .brand{flex:0 0 100%}
  .topnav{flex:0 0 100%;gap:16px;font-size:.8rem;overflow-x:auto;overscroll-behavior-x:contain;scrollbar-width:none;-ms-overflow-style:none;padding-bottom:1px;-webkit-mask-image:linear-gradient(to right,#000 calc(100% - 16px),transparent);mask-image:linear-gradient(to right,#000 calc(100% - 16px),transparent)}
  .topnav::-webkit-scrollbar{display:none}
}
@media (max-width:400px){ .topnav{gap:13px;font-size:.76rem} .wrap{padding:0 16px} }
"""

HUB_CSS = """
.hero{padding:76px 0 56px;background:linear-gradient(180deg,var(--paper-2),var(--paper))}
.hero h1{font-family:var(--display);font-size:clamp(2.1rem,5.4vw,3.4rem);line-height:1.22;margin:14px 0 0;letter-spacing:-.02em}
.hero .lead{font-family:var(--display);font-size:clamp(1.05rem,2.2vw,1.3rem);color:var(--teal-dark);margin:16px 0 0}
.hero p.intro{max-width:52rem;color:var(--muted);margin:20px 0 0}
.progress{display:flex;align-items:baseline;gap:12px;margin-top:30px;font-family:var(--mono);font-size:.8rem;color:var(--muted)}
.progress b{font-size:1.9rem;color:var(--ink);font-family:var(--display)}
.keyvis{margin:34px 0 4px;border-radius:14px;overflow:hidden;background:#0d1621;border:1px solid rgba(0,0,0,.08)}
.keyvis img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.keyvis figcaption{padding:14px 18px 17px;font-size:.84rem;line-height:1.65;color:rgba(255,255,255,.62);font-family:var(--mono)}
.worldlink{margin:14px 0 0;font-family:var(--mono);font-size:.86rem}
.worldlink a{color:var(--teal-dark);text-decoration:none;font-weight:600;border-bottom:1px solid rgba(0,0,0,.18);padding-bottom:2px}
.bar{flex:1;max-width:260px;height:6px;background:var(--lime);border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--teal)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(292px,1fr));gap:26px;padding:56px 0 8px}
.card{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--paper);text-decoration:none;
  display:flex;flex-direction:column;transition:transform .18s ease,box-shadow .18s ease}
.card:hover{transform:translateY(-3px);box-shadow:0 14px 34px rgba(31,45,64,.11)}
.card .thumb{aspect-ratio:16/9;background:var(--deep);overflow:hidden}
.card .thumb img{width:100%;height:100%;object-fit:cover}
.card .body{padding:20px 22px 24px;display:flex;flex-direction:column;gap:9px;flex:1}
.card .no{font-family:var(--mono);font-size:.73rem;letter-spacing:.1em;color:var(--teal-dark)}
.card h2{font-family:var(--display);font-size:1.42rem;margin:0;letter-spacing:-.01em}
.card .en{font-family:var(--mono);font-size:.76rem;color:var(--muted);letter-spacing:.05em;margin-top:-4px}
.card .log{color:var(--muted);font-size:.9rem;margin:2px 0 0;flex:1}
.card .meta{display:flex;gap:10px;align-items:center;font-size:.75rem;color:var(--muted);font-family:var(--mono);
  border-top:1px solid var(--line);padding-top:12px;margin-top:6px}
.tag{background:var(--lime);color:var(--teal-dark);border-radius:99px;padding:3px 10px;font-size:.72rem}
.soon{border:1px dashed var(--line);border-radius:14px;display:flex;align-items:center;justify-content:center;
  min-height:190px;color:var(--muted);font-family:var(--mono);font-size:.82rem;text-align:center;padding:24px;background:var(--paper-2)}
"""

WORK_CSS = """
.whero{background:var(--deep);color:#fff}
.whero .inner{display:grid;grid-template-columns:1.05fr .95fr;align-items:center;max-width:var(--max);margin:0 auto}
.whero .art{background:#0d1621;display:flex;align-items:center}
.whero .art img{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
.whero .txt{padding:52px 40px 50px}
.whero .no{font-family:var(--mono);font-size:.75rem;letter-spacing:.14em;color:var(--orange)}
.whero h1{font-family:var(--display);font-size:clamp(2.2rem,5vw,3.1rem);margin:14px 0 6px;letter-spacing:-.02em;line-height:1.18}
.whero .en{font-family:var(--mono);font-size:.86rem;letter-spacing:.14em;color:rgba(255,255,255,.62)}
.whero .log{font-family:var(--display);font-size:1.08rem;color:rgba(255,255,255,.9);margin:22px 0 0;line-height:1.7}
.whero .facts{display:flex;flex-wrap:wrap;gap:8px 20px;margin:26px 0 0;font-family:var(--mono);font-size:.76rem;color:rgba(255,255,255,.6)}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}
.btn{display:inline-flex;align-items:center;gap:8px;border-radius:99px;padding:11px 22px;font-size:.87rem;
  font-weight:600;text-decoration:none;border:1px solid rgba(255,255,255,.28);color:#fff}
.btn.primary{background:var(--orange);border-color:var(--orange);color:#2b1a12}
.btn.disabled{opacity:.42;pointer-events:none}
.synopsis{padding:56px 0 12px}
.synopsis .k{font-family:var(--mono);font-size:.74rem;letter-spacing:.14em;color:var(--teal-dark)}
.synopsis p{max-width:var(--read);font-size:1rem;color:var(--muted);margin:14px 0 0}
.theme{font-family:var(--display);font-size:1.22rem;color:var(--ink);margin:26px 0 0;padding-left:16px;border-left:2px solid var(--orange)}
.story{padding:14px 0 0}
.story .inner{max-width:var(--read);margin:0 auto}
.story h2{font-family:var(--display);font-size:1.6rem;margin:64px 0 20px;letter-spacing:-.01em}
.story h3{font-family:var(--display);font-size:1.24rem;margin:44px 0 14px}
.story p{font-family:var(--display);font-size:1.06rem;line-height:2.0;margin:0 0 1.35em;word-break:keep-all}
.story blockquote{margin:28px 0;padding:2px 0 2px 20px;border-left:2px solid var(--teal);color:var(--teal-dark);font-family:var(--display);font-style:normal}
.story hr{border:0;height:1px;background:var(--line);margin:52px 0}
.story img{border-radius:10px;margin:34px auto;box-shadow:0 10px 30px rgba(31,45,64,.10)}
@media (min-width:900px){ .story img{width:min(58rem,92vw);max-width:none;margin-left:calc((44rem - min(58rem,92vw))/2)} }
.notice{max-width:var(--read);margin:40px auto;border:1px solid var(--line);border-left:3px solid var(--orange);
  border-radius:0 10px 10px 0;padding:22px 26px;background:var(--paper-2)}
.notice b{display:block;font-family:var(--display);font-size:1.05rem;margin-bottom:6px}
.notice p{margin:0;color:var(--muted);font-size:.9rem}
.gallery{padding:64px 0 0}
.gallery h2{font-family:var(--display);font-size:1.5rem;margin:0 0 6px}
.gallery .sub{color:var(--muted);font-size:.88rem;margin:0 0 26px}
.gcols{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.gcols img{border-radius:8px;aspect-ratio:16/9;object-fit:cover;background:var(--deep)}
.pager{display:flex;justify-content:space-between;gap:16px;margin:72px 0 0;padding-top:26px;border-top:1px solid var(--line)}
.pager a{text-decoration:none;font-size:.9rem;color:var(--teal-dark);font-weight:600}
.pager span{color:var(--muted);font-size:.9rem}
@media (max-width:860px){ .whero .inner{grid-template-columns:1fr} .whero .txt{padding:38px 22px 42px} }
"""

WORLD_CSS = """
.hero{padding:70px 0 44px;background:linear-gradient(180deg,var(--paper-2),var(--paper))}
.hero h1{font-family:var(--display);font-size:clamp(2rem,5vw,3.1rem);line-height:1.22;margin:12px 0 0;letter-spacing:-.02em}
.hero .lead{font-family:var(--display);font-size:clamp(1.02rem,2.1vw,1.26rem);color:var(--teal-dark);margin:16px 0 0}
.hero p.intro{max-width:50rem;color:var(--muted);margin:18px 0 0}
.eyebrow{font-family:var(--mono);font-size:.74rem;letter-spacing:.15em;color:var(--orange)}
.whero-img{margin:0 0 6px;border-radius:14px;overflow:hidden;background:#0d1621}
.whero-img img{width:100%;aspect-ratio:21/9;object-fit:cover;display:block}
.wsec{margin:58px 0 0}
.wsec .inner{display:grid;grid-template-columns:minmax(0,46%) 1fr;gap:30px;align-items:start}
.wsec figure{margin:0;border-radius:12px;overflow:hidden;background:#0d1621;border:1px solid rgba(0,0,0,.08)}
.wsec figure img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.wsec figcaption{padding:11px 14px 14px;font-family:var(--mono);font-size:.76rem;line-height:1.55;color:rgba(255,255,255,.6)}
.wsec h2{font-family:var(--display);font-size:1.52rem;letter-spacing:-.015em;margin:0 0 14px}
.wsec p{margin:0 0 14px;line-height:1.85;color:var(--ink)}
.wsec p:last-child{margin-bottom:0}
.wback{margin:64px 0 0;padding:26px 0 0;border-top:1px solid rgba(0,0,0,.1)}
.wback a{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:.84rem;color:var(--teal-dark);text-decoration:none;font-weight:600}
@media (max-width:820px){ .wsec .inner{grid-template-columns:1fr} .whero-img img{aspect-ratio:16/9} }
"""

def head(lang, title, desc, og, root, hubhref, altko, alten, self_url, pagecss, switch_href):
    t = T[lang]
    nav = "".join('<a href="%s%s">%s</a>' % (root, h, l) for h, l in t["nav"])
    nav += '<a href="%s" aria-current="page">%s</a>' % (hubhref, t["hubNav"])
    nav += '<a class="langsw" href="%s" hreflang="%s" title="%s">%s</a>' % (
        switch_href, "en" if lang == "ko" else "ko", t["switchTitle"], t["switch"])
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}" />
<link rel="canonical" href="{self_url}" />
<link rel="alternate" hreflang="ko" href="{altko}" />
<link rel="alternate" hreflang="en" href="{alten}" />
<link rel="alternate" hreflang="x-default" href="{altko}" />
<meta property="og:title" content="{html.escape(title)}" />
<meta property="og:description" content="{html.escape(desc)}" />
<meta property="og:image" content="{og}" />
<meta property="og:locale" content="{'ko_KR' if lang=='ko' else 'en_US'}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&family=Noto+Serif+KR:wght@400;500;600;700&display=swap" rel="stylesheet" />
<style>{BASE_CSS}</style>
<style>{pagecss}</style>
</head>
<body>
<header class="topbar"><div class="wrap">
  <a class="brand" href="{root}index.html">{T[lang]["brand"]}</a>
  <nav class="topnav">{nav}</nav>
</div></header>
"""

def foot(root, credit, homelabel):
    return ('<footer><div class="wrap">\n  <span>%s</span>\n'
            '  <span><a href="%sindex.html" style="color:var(--teal-dark)">%s</a> · osiki999@gmail.com</span>\n'
            '</div></footer>\n</body></html>\n') % (html.escape(credit), root, homelabel)

# ─────────────────────────── 본문 ───────────────────────────
def render_manuscript(slug, name, asset_prefix):
    path = os.path.join(MSRC, name)
    if not os.path.exists(path):
        return None
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"^.*\.mp4\).*$", "", raw, flags=re.M)          # 로컬 영상 링크 제거
    def fix(m):
        base = os.path.splitext(os.path.basename(m.group(2)))[0]
        return "![%s](%s%s/%s.jpg)" % (m.group(1), asset_prefix, slug, base)
    raw = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", fix, raw)
    body = mdlib.markdown(raw, extensions=["extra", "sane_lists", "nl2br"])
    return body.replace("<img ", '<img loading="lazy" ')

def gallery_files(slug, cover, end):
    d = os.path.join(ASSET, slug)
    if not os.path.isdir(d):
        return []
    # 언어별 표지/엔딩은 양쪽 모두 갤러리에서 제외한다
    skip = {cover, end, "00-cover.jpg", "99-ending.jpg",
            "00-en-cover.jpg", "99-en-ending.jpg", "00-teaser.jpg"}
    return [os.path.basename(p) for p in sorted(glob.glob(os.path.join(d, "*.jpg")))
            if os.path.basename(p) not in skip and "-en-" not in os.path.basename(p)]

def buttons(w, lang):
    t = T[lang]; out = []
    blog = (val(w, lang, "blogUrl") or "").strip()
    if blog:
        out.append('<a class="btn" href="%s" target="_blank" rel="noreferrer">%s</a>' % (html.escape(blog), t["blog"]))
    v = val(w, lang, "video") or {}
    url, note = (v.get("naverUrl") or "").strip(), v.get("note", "")
    if url:
        out.append('<a class="btn primary" href="%s" target="_blank" rel="noreferrer">%s<span style="opacity:.7;font-weight:400"> · %s</span></a>'
                   % (html.escape(url), t["watch"], html.escape(note)))
    # 링크가 없으면 비활성 버튼을 만들지 않고 감춘다.
    # 한국어판은 영상이 소설 포스트 안에 들어 있어 블로그 버튼 하나로 충분하다.
    return "\n      ".join(out)

# ─────────────────────────── 페이지 ───────────────────────────
def build_work(cfg, i, lang):
    t = T[lang]; works = cfg["works"]; w = works[i]; s = cfg["series"]
    base = cfg["baseUrl"]; slug = w["slug"]
    sd = s.get("en", s) if lang == "en" else s
    root   = "../../" if lang == "en" else "../"
    apre   = root + "assets/fiction/"
    hub    = "../fiction.html"
    switch = ("../../fiction/%s.html" % slug) if lang == "en" else ("../en/fiction/%s.html" % slug)
    altko  = "%s/fiction/%s.html" % (base, slug)
    alten  = "%s/en/fiction/%s.html" % (base, slug)
    self_u = alten if lang == "en" else altko

    title_ko = w["titleKo"]; title = title_ko if lang == "ko" else w["titleEn"]
    cover = apre + slug + "/" + val(w, lang, "coverImage")
    label = val(w, lang, "seriesLabel"); logline = val(w, lang, "logline")
    doc = [head(lang, "%s %s · %s" % (label, title, sd["title"]), logline,
                "%s/assets/fiction/%s/%s" % (base, slug, val(w, lang, "coverImage")),
                root, hub, altko, alten, self_u, WORK_CSS, switch)]

    doc.append('<section class="whero"><div class="inner">')
    doc.append('  <div class="art"><img src="%s" alt="%s" /></div>' % (cover, html.escape(title)))
    doc.append('  <div class="txt">')
    doc.append('    <div class="no">%s · %s</div>' % (html.escape(label), html.escape(val(w, lang, "status", ""))))
    han = (' <span style="font-size:.62em;opacity:.55">%s</span>' % w["titleHanja"]) if (lang == "ko" and w.get("titleHanja")) else ""
    doc.append('    <h1>%s%s</h1>' % (html.escape(title), han))
    doc.append('    <div class="en">%s</div>' % html.escape(w["titleEn"] if lang == "ko" else title_ko))
    doc.append('    <p class="log">%s</p>' % html.escape(logline))
    doc.append('    <div class="facts"><span>%s</span><span>%s</span><span>%s</span></div>'
               % (t["kind"], html.escape(val(w, lang, "runtime")), html.escape(w["published"])))
    doc.append('    <div class="btns">\n      %s\n    </div>' % buttons(w, lang))
    doc.append('  </div>\n</div></section>')

    doc.append('<div class="wrap"><section class="synopsis">')
    doc.append('  <div class="k">%s</div>' % t["synopsis"])
    doc.append('  <p>%s</p>' % html.escape(val(w, lang, "synopsis")))
    if val(w, lang, "theme"):
        doc.append('  <p class="theme">%s</p>' % html.escape(val(w, lang, "theme")))
    doc.append('</section></div>')

    ms = w.get("manuscriptEn") if lang == "en" else w.get("manuscriptKo")
    body = render_manuscript(slug, ms, apre) if ms else None
    doc.append('<div class="wrap"><section class="story"><div class="inner">')
    if body:
        doc.append('<hr class="rule" style="margin:52px 0 8px" />')
        doc.append(body)
        end = val(w, lang, "endImage")
        if end:
            doc.append('<img loading="lazy" src="%s%s/%s" alt="%s" />' % (apre, slug, end, html.escape(title)))
    else:
        h, p = t["noText"]
        doc.append('<div class="notice"><b>%s</b><p>%s</p></div>' % (h, p))
    doc.append('</div></section></div>')

    gal = [] if (body and "<img" in body) else gallery_files(slug, val(w, lang, "coverImage"), val(w, lang, "endImage"))
    if gal:
        doc.append('<div class="wrap"><section class="gallery">')
        doc.append('  <h2>%s</h2><p class="sub">%s · %s</p>' % (t["stills"], html.escape(title), t["scenes"] % len(gal)))
        doc.append('  <div class="gcols">')
        for g in gal:
            doc.append('    <img loading="lazy" src="%s%s/%s" alt="%s" />' % (apre, slug, g, html.escape(title)))
        doc.append('  </div></section></div>')

    pv = works[i - 1] if i > 0 else None
    nx = works[i + 1] if i < len(works) - 1 else None
    doc.append('<div class="wrap"><nav class="pager">')
    doc.append('<a href="%s.html">← %s</a>' % (pv["slug"], html.escape(pv["titleKo"] if lang == "ko" else pv["titleEn"]))
               if pv else '<a href="%s">%s</a>' % (hub, t["index"]))
    doc.append('<a href="%s.html">%s →</a>' % (nx["slug"], html.escape(nx["titleKo"] if lang == "ko" else nx["titleEn"]))
               if nx else '<span>%s</span>' % t["nextSoon"])
    doc.append('</nav></div>')
    doc.append(foot(root, sd["credit"], t["home"]))

    out = os.path.join(ROOT, "en", "fiction", slug + ".html") if lang == "en" else os.path.join(ROOT, "fiction", slug + ".html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(doc))
    return out, bool(body), len(gal)

def build_world(cfg, lang):
    wp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world.json")
    if not os.path.exists(wp):
        return None
    w = json.load(io.open(wp, encoding="utf-8"))
    t = T[lang]; s = cfg["series"]; base = cfg["baseUrl"]
    root   = "../" if lang == "en" else ""
    page   = "fiction-world.html"
    switch = ("../" if lang == "en" else "en/") + page
    altko  = base + "/" + page; alten = base + "/en/" + page
    title  = w["titleEn"] if lang == "en" else w["titleKo"]
    lead   = w["leadEn"]  if lang == "en" else w["leadKo"]
    intro  = w["introEn"] if lang == "en" else w["introKo"]
    og     = base + "/" + s.get("ogImage", "assets/og/og-fiction.jpg")
    doc = [head(lang, title, intro[:150], og, root, root + "fiction.html",
                altko, alten, (alten if lang == "en" else altko), WORLD_CSS, switch)]
    doc.append('<section class="hero"><div class="wrap">')
    doc.append('  <div class="eyebrow">%s</div>' % ("SETTING" if lang == "en" else "SETTING · 설정"))
    doc.append('  <h1>%s</h1>' % html.escape(title))
    doc.append('  <p class="lead">%s</p>' % html.escape(lead))
    doc.append('  <p class="intro">%s</p>' % html.escape(intro))
    doc.append('</div></section>')
    hi = w.get("heroImage")
    if hi:
        alt = w.get("heroAltEn" if lang == "en" else "heroAltKo", "")
        doc.append('<div class="wrap"><figure class="whero-img"><img src="%s%s" alt="%s" /></figure></div>'
                   % (root, hi, html.escape(alt)))
    doc.append('<div class="wrap">')
    for sec in w["sections"]:
        c = sec["en"] if lang == "en" else sec["ko"]
        doc.append('<section class="wsec"><div class="inner">')
        doc.append('  <figure><img loading="lazy" src="%s%s" alt="%s" />' % (root, sec["image"], html.escape(c["title"])))
        if c.get("caption"):
            doc.append('    <figcaption>%s</figcaption>' % html.escape(c["caption"]))
        doc.append('  </figure>')
        doc.append('  <div><h2>%s</h2>' % html.escape(c["title"]))
        for para in c["body"].split("\n\n"):
            doc.append('    <p>%s</p>' % html.escape(para.strip()))
        doc.append('  </div>')
        doc.append('</div></section>')
    backlabel = "Back to the series" if lang == "en" else "연작 전체 보기"
    doc.append('<div class="wback"><a href="%sfiction.html">← %s</a></div>' % (root, backlabel))
    doc.append('</div>')
    sd = s.get("en", s) if lang == "en" else s
    doc.append(foot(root, sd.get("credit", s.get("credit", "")), t.get("home", "Home" if lang == "en" else "홈")))
    out = (os.path.join("en", page) if lang == "en" else page)
    io.open(os.path.join(ROOT, out), "w", encoding="utf-8").write("\n".join(doc))
    print("  %-40s 세계관 %d절" % (out, len(w["sections"])))
    return out

def build_hub(cfg, lang):
    t = T[lang]; s = cfg["series"]; works = cfg["works"]; base = cfg["baseUrl"]
    sd = s.get("en", s) if lang == "en" else s
    root   = "../" if lang == "en" else ""
    apre   = root + "assets/fiction/"
    hub    = "fiction.html"
    switch = "../fiction.html" if lang == "en" else "en/fiction.html"
    altko  = base + "/fiction.html"; alten = base + "/en/fiction.html"
    hub_og = s.get("ogImage")
    hub_og = (base + "/" + hub_og) if hub_og else \
             ("%s/assets/fiction/%s/%s" % (base, works[0]["slug"], val(works[0], lang, "coverImage")))
    doc = [head(lang, "%s · %s" % (sd["title"], sd["socialTitle"]), sd["intro"][:150],
                hub_og,
                root, hub, altko, alten, (alten if lang == "en" else altko), HUB_CSS, switch)]
    doc.append('<section class="hero"><div class="wrap">')
    doc.append('  <div class="eyebrow">%s</div>' % (t["eyebrow"] % s["planned"]))
    doc.append('  <h1>%s</h1>' % html.escape(sd["socialTitle"]))
    doc.append('  <p class="lead">%s</p>' % html.escape(sd["lead"]))
    doc.append('  <p class="intro">%s</p>' % html.escape(sd["intro"]))
    doc.append('  <div class="progress"><b>%d</b><span>%s</span><span class="bar"><i style="width:%.0f%%"></i></span></div>'
               % (len(works), t["progress"] % s["planned"], 100.0 * len(works) / s["planned"]))
    doc.append('</div></section>')
    kv = s.get("keyVisual")
    if kv:
        alt = kv.get("altEn" if lang == "en" else "altKo", "")
        cap = kv.get("captionEn" if lang == "en" else "captionKo", "")
        doc.append('<div class="wrap"><figure class="keyvis">')
        doc.append('  <img src="%s%s" alt="%s" />' % (root, kv["src"], html.escape(alt)))
        if cap:
            doc.append('  <figcaption>%s</figcaption>' % html.escape(cap))
        doc.append('</figure></div>')
    wlabel = ("Two peoples, a gate of three layers, a 0.4 degree — read the setting"
              if lang == "en" else "두 종족, 세 겹의 관문, 0.4도 — 세계관 읽기")
    doc.append('<div class="wrap"><p class="worldlink"><a href="%sfiction-world.html">%s →</a></p></div>'
               % (root, html.escape(wlabel)))
    doc.append('<div class="wrap"><div class="grid">')
    for w in works:
        title = w["titleKo"] if lang == "ko" else w["titleEn"]
        sub   = w["titleEn"] if lang == "ko" else w["titleKo"]
        doc.append('  <a class="card" href="fiction/%s.html">' % w["slug"])
        doc.append('    <span class="thumb"><img loading="lazy" src="%s%s/%s" alt="%s" /></span>'
                   % (apre, w["slug"], val(w, lang, "coverImage"), html.escape(title)))
        doc.append('    <span class="body">')
        doc.append('      <span class="no">%s</span>' % html.escape(val(w, lang, "seriesLabel")))
        doc.append('      <h2>%s</h2><span class="en">%s</span>' % (html.escape(title), html.escape(sub)))
        doc.append('      <span class="log">%s</span>' % html.escape(val(w, lang, "logline")))
        doc.append('      <span class="meta"><span class="tag">%s</span><span>%s</span><span>%s</span></span>'
                   % (html.escape(val(w, lang, "status", "")), html.escape(val(w, lang, "runtime")), html.escape(w["published"])))
        doc.append('    </span>\n  </a>')
    if s["planned"] > len(works):
        doc.append('  <div class="soon">%s</div>' % (t["soon"] % (len(works) + 1, s["planned"])))
    doc.append('</div></div>')
    doc.append(foot(root, sd["credit"], t["home"]))
    out = os.path.join(ROOT, "en", "fiction.html") if lang == "en" else os.path.join(ROOT, "fiction.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(doc))
    return out

def main():
    cfg = json.load(open(CFG, encoding="utf-8"))
    for lang in ("ko", "en"):
        print("[%s]" % lang)
        for i in range(len(cfg["works"])):
            p, has, ng = build_work(cfg, i, lang)
            print("  %-40s 본문 %s · 갤러리 %2d" % (os.path.relpath(p, ROOT), "O" if has else "-", ng))
        print("  %-40s 허브" % os.path.relpath(build_hub(cfg, lang), ROOT))
        build_world(cfg, lang)

if __name__ == "__main__":
    main()
