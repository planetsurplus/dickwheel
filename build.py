#!/usr/bin/env python3
"""Build the dickwheel.com static site from data/editions/*.json.

Usage:  python3 build.py            -> writes ./public
Env:    SITE_URL   full public URL, e.g. https://fairbankscrime.com  (for RSS + canonical links)
        BASE_PATH  path prefix, "/" for a custom domain, "/repo-name/" for a GitHub project page
No third-party packages required.
"""
import json, os, shutil, sys, datetime as dt
from html import escape as e
from pathlib import Path
from email.utils import format_datetime

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "public"
SITE_NAME = "Allegedly, these crimes occurred, but maybe not."
SITE_URL = os.environ.get("SITE_URL", "https://dickwheel.com").rstrip("/")
BASE = os.environ.get("BASE_PATH", "/")
if not BASE.endswith("/"):
    BASE += "/"

CATEGORIES = [("all", "All"), ("violent", "Violent"), ("property", "Property"), ("dui", "DUI / traffic"),
              ("drug", "Drugs"), ("court", "Courts"), ("other", "Other")]
SEVERITY_CHIP = {"felony": ("felony", "Felony"), "misdemeanor": ("misdemeanor", "Misdemeanor")}
SOURCE_CHIP = {"read": ("ok", "Read"), "stale": ("stale", "Stale"), "not reached": ("not-reached", "Not reached")}


# ---------- helpers ----------
def load_editions():
    eds = []
    for f in sorted((DATA / "editions").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except json.JSONDecodeError as err:
            sys.exit(f"ERROR: {f.name} is not valid JSON: {err}")
        for key in ("date", "entries"):
            if key not in d:
                sys.exit(f"ERROR: {f.name} is missing '{key}'")
        if f.stem != d["date"]:
            sys.exit(f"ERROR: {f.name} has date {d['date']} — file name must match")
        eds.append(d)
    eds.sort(key=lambda d: d["date"], reverse=True)
    return eds


def pdate(s):
    return dt.date.fromisoformat(s)


def long_date(s):
    d = pdate(s)
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}, {d.year}"


def short_date(s):
    d = pdate(s)
    return f"{d.strftime('%b')}. {d.day}" if d.month != 5 else f"May {d.day}"


def ed_url(date):
    return f"editions/{date}/"


def days_since(iso, ref):
    try:
        return (pdate(ref) - pdate(iso)).days
    except Exception:
        return None


def write(path, html):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html)


# ---------- page shell ----------
NAV = [("", "Latest"), ("archive/", "Archive"), ("cases/", "Open cases"), ("search/", "Search"),
       ("corrections/", "Corrections"), ("wheel/", "Motive Wheel"), ("about/", "About")]


def page(path, title, body, description="", active=""):
    full_title = f"{title} · {SITE_NAME}" if title != SITE_NAME else SITE_NAME
    nav = "".join(
        f'<li><a href="{BASE}{href}"{" aria-current=page" if href == active else ""}>{label}</a></li>' for href, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description or 'Daily crime and court record for Fairbanks and Interior Alaska, compiled from primary sources.')}">
<link rel="canonical" href="{SITE_URL}{BASE}{path}">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{BASE}feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Public+Sans:wght@400;600;800&family=Spectral:wght@600&display=swap">
<link rel="stylesheet" href="{BASE}static/style.css">
<script>try{{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script>
</head>
<body data-base="{BASE}">
<header class="site-head"><div class="wrap">
  <p class="org">Interior Alaska · Compiled daily from primary records</p>
  <p class="brand"><a href="{BASE}">{SITE_NAME}</a></p>
</div></header>
<nav class="top" aria-label="Site"><ul>{nav}</ul></nav>
<div class="wrap">
{body}
<footer class="site-foot">
  <p>This site republishes information from public law-enforcement and court records for Fairbanks and roughly 100 miles around it. An arrest or charge is an accusation, not a finding of guilt; everyone named is presumed innocent unless and until proven guilty in court.</p>
  <p>Errors are corrected openly on the <a href="{BASE}corrections/">corrections page</a>. <a href="{BASE}feed.xml">RSS feed</a> · <button class="theme-toggle" type="button">Light / dark</button></p>
</footer>
</div>
<button type="button" class="wheel-fab" aria-haspopup="dialog" aria-controls="wheel-dialog"><svg viewBox="0 0 64 64" aria-hidden="true" class="wheel-ico"><g class="spinner">
<path d="M32 32 L32 4 A28 28 0 0 1 51.8 12.2Z" fill="#e0303b"/><path d="M32 32 L51.8 12.2 A28 28 0 0 1 60 32Z" fill="#f5d90a"/>
<path d="M32 32 L60 32 A28 28 0 0 1 51.8 51.8Z" fill="#3a7bff"/><path d="M32 32 L51.8 51.8 A28 28 0 0 1 32 60Z" fill="#1b1e2b"/>
<path d="M32 32 L32 60 A28 28 0 0 1 12.2 51.8Z" fill="#e0303b"/><path d="M32 32 L12.2 51.8 A28 28 0 0 1 4 32Z" fill="#f5d90a"/>
<path d="M32 32 L4 32 A28 28 0 0 1 12.2 12.2Z" fill="#3a7bff"/><path d="M32 32 L12.2 12.2 A28 28 0 0 1 32 4Z" fill="#1b1e2b"/></g>
<circle cx="32" cy="32" r="28" fill="none" stroke="#f2a33a" stroke-width="3"/><circle cx="32" cy="32" r="7" fill="#11131c" stroke="#f2a33a" stroke-width="2.5"/>
<path d="M25 0 H39 L32 11Z" fill="#ecebe6" stroke="#11131c" stroke-width="1.5"/></svg><span class="wheel-fab-label">Why'd they do it?</span></button>
<dialog id="wheel-dialog" class="wheel-dialog" aria-label="Motive Wheel">
<button type="button" class="wheel-close" aria-label="Close the Motive Wheel">&times;</button>
<iframe class="wheel-embed" data-src="{BASE}wheel/?embed=1" title="Motive Wheel: spin for a joke motive"></iframe>
<p class="wheel-note">Satire. <a href="{BASE}wheel/">Open the full-size wheel &rarr;</a></p>
</dialog>
<script src="{BASE}static/site.js"></script>
</body>
</html>"""


# ---------- components ----------
def render_entry(en, edition_date):
    chips = []
    if en.get("severity") in SEVERITY_CHIP:
        cls, label = SEVERITY_CHIP[en["severity"]]
        chips.append(f'<span class="chip {cls}">{label}</span>')
    chips.append(f'<span class="chip agency">{e(en.get("agency", ""))}</span>')
    for t in en.get("tags", []):
        chips.append(f'<span class="chip">{e(t)}</span>')
    gutter = [f'<span class="d">{short_date(en["date"])}</span>']
    if en.get("time"):
        gutter.append(f'<span>{e(en["time"])}</span>')
    if en.get("place"):
        gutter.append(f'<span>{e(en["place"])}</span>')
    gutter += [f'<span class="case">{e(c)}</span>' for c in en.get("cases", [])]
    paras = "".join(f"<p>{e(p)}</p>" for p in en.get("body", []))
    srcs = en.get("sources", [])
    src_html = ""
    if srcs:
        links = " · ".join(f'<a href="{e(s["url"])}" rel="noopener">{e(s["label"])}</a>' if s.get("url") else e(s["label"]) for s in srcs)
        src_html = f'<p class="src">Source: {links}</p>'
    return f"""<article class="entry" id="{e(en['id'])}" data-cat="{e(en.get('category', 'other'))}">
<div class="gutter">{''.join(gutter)}</div>
<div><h3><a href="{BASE}{ed_url(edition_date)}#{e(en['id'])}" style="color:inherit;text-decoration:none">{e(en['title'])}</a></h3>
<div class="chips">{''.join(chips)}</div>{paras}{src_html}</div></article>"""


def render_filings(f):
    if not f:
        return ""
    rows = "".join(f'<tr><td>{e(c["court"])}</td><td class="num">{c["count"]}</td></tr>' for c in f.get("courts", []))
    total = sum(c["count"] for c in f.get("courts", []))
    new = ""
    if f.get("new"):
        fel_chip = '<span class="chip felony">Felony</span> '
        nrows = "".join(
            f'<tr><td class="case">{e(n["case"])}</td><td>{e(n["defendant"])}</td><td>'
            f'{fel_chip if n.get("felony") else ""}{e(n["charges"])}</td></tr>'
            for n in f["new"])
        new = f'<div class="tw"><table><thead><tr><th>Case</th><th>Defendant</th><th>Charges as filed</th></tr></thead><tbody>{nrows}</tbody></table></div>'
    return f"""<section id="filings"><h2>Court filings <span class="count">{e(f.get('window', ''))} · {total} cases</span></h2>
<div class="tw"><table><thead><tr><th>Court</th><th>Cases filed</th></tr></thead><tbody>{rows}</tbody></table></div>
{new}</section>"""


def render_cases(cases, ref_date):
    cards = []
    for c in cases:
        ds = days_since(c.get("last_docket", ""), ref_date)
        last = f'{short_date(c["last_docket"])} ({ds} day{"s" if ds != 1 else ""} ago)' if ds is not None else e(c.get("last_docket", "—"))
        lvl = c.get("level", "")
        chip_cls = "felony" if "felony" in lvl.lower() else ""
        cards.append(f"""<article class="card" id="{e(c['case'])}"><span class="case">{e(c['case'])}</span>
<span class="who">{e(c['defendant'])}</span>{f'<div class="chips"><span class="chip {chip_cls}">{e(lvl)}</span></div>' if lvl else ''}
<p>{e(c.get('charges', ''))}</p>
<dl class="kv"><dt>Next</dt><dd>{e(c.get('next', '—'))}</dd><dt>Judge</dt><dd>{e(c.get('judge', '—'))}</dd><dt>Last docket</dt><dd>{last}</dd></dl></article>""")
    return f'<div class="cases">{"".join(cards)}</div>'


def render_sources(srcs):
    if not srcs:
        return ""
    rows = []
    for s in srcs:
        cls, label = SOURCE_CHIP.get(s.get("status", "read"), ("", s.get("status", "")))
        rows.append(f'<tr><td><a href="{e(s["url"])}" rel="noopener">{e(s["name"])}</a></td>'
                    f'<td><span class="chip {cls}">{label}</span></td><td>{e(s.get("note", ""))}</td></tr>')
    return f"""<section id="sources"><h2>Sources checked <span class="count">{len(srcs)} sources</span></h2>
<div class="tw"><table><thead><tr><th>Source</th><th>Status</th><th>Note</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>"""


def sidebar(ed, editions):
    n = len(ed["entries"])
    fel = sum(1 for x in ed["entries"] if x.get("severity") == "felony")
    filings = sum(c["count"] for c in (ed.get("filings") or {}).get("courts", [])) if ed.get("filings") else "—"
    cases = len(ed.get("open_cases") or []) or "—"
    com = ed.get("commentary")
    if com:
        com_html = f"""<section class="panel commentary"><p class="label">Commentary</p>
<h3>{e(com.get('title', ''))}</h3>{''.join(f'<p>{e(p)}</p>' for p in com.get('body', []))}
<p class="presumption">Opinion. Kept separate from the record.</p></section>"""
    else:
        com_html = f"""<section class="panel commentary"><p class="label">Commentary</p>
<p class="placeholder">Commentary column coming soon.</p></section>"""
    recent = "".join(
        f'<li><a href="{BASE}{ed_url(x["date"])}">{short_date(x["date"])}</a><span class="n">{len(x["entries"])} entries</span></li>'
        for x in editions[:8])
    return f"""<aside class="side">
<section class="panel"><h2>This edition</h2><div class="stats">
<div><span class="v">{n}</span><span class="l">Entries</span></div>
<div><span class="v">{fel}</span><span class="l">Felony items</span></div>
<div><span class="v">{filings}</span><span class="l">Court filings (week)</span></div>
<div><span class="v">{cases}</span><span class="l">Open cases</span></div></div></section>
{com_html}
<section class="panel"><h2>Recent editions</h2><ul>{recent}</ul>
<p style="margin-top:10px"><a href="{BASE}archive/">Full archive →</a></p></section>
</aside>"""


def edition_body(ed, editions, is_home=False):
    idx = [x["date"] for x in editions].index(ed["date"])
    newer = editions[idx - 1]["date"] if idx > 0 else None
    older = editions[idx + 1]["date"] if idx + 1 < len(editions) else None
    cats_present = {x.get("category", "other") for x in ed["entries"]}
    filt = "".join(
        f'<button type="button" data-cat="{k}" aria-pressed="{"true" if k == "all" else "false"}">{v}</button>'
        for k, v in CATEGORIES if k == "all" or k in cats_present)
    entries = "".join(render_entry(x, ed["date"]) for x in ed["entries"])
    cases = ""
    if ed.get("open_cases"):
        cases = f'<section id="cases"><h2>Open cases <span class="count">{len(ed["open_cases"])} tracked · re-checked this edition</span></h2>{render_cases(ed["open_cases"], ed["date"])}</section>'
    daynav = f"""<div class="daynav"><span>{f'<a href="{BASE}{ed_url(older)}">← {short_date(older)}</a>' if older else ''}</span>
<span>{f'<a href="{BASE}{ed_url(newer)}">{short_date(newer)} →</a>' if newer else ''}</span></div>"""
    main = f"""<main>
<p class="dateline"><b>{long_date(ed['date'])}</b><span>Compiled {e(ed.get('compiled', ''))}</span><span>Covers {e(ed.get('window', ''))}</span></p>
<h1 class="page">{'Today in Interior Alaska' if is_home else 'Edition of ' + long_date(ed['date'])}</h1>
<p class="lede">{e(ed.get('summary', ''))}</p>
<p class="presumption">Everyone named is arrested or charged, not convicted.</p>
<section id="latest"><h2>Entries <span class="count">{len(ed['entries'])} items</span></h2>
<div class="filters" role="group" aria-label="Filter by category">{filt}</div>
<div class="entries">{entries}</div></section>
{render_filings(ed.get('filings'))}
{cases}
{render_sources(ed.get('sources'))}
{daynav}
</main>"""
    return f'<div class="layout">{main}{sidebar(ed, editions)}</div>'


# ---------- pages ----------
def build():
    editions = load_editions()
    if not editions:
        sys.exit("ERROR: no editions in data/editions/")
    corrections = json.loads((DATA / "corrections.json").read_text()) if (DATA / "corrections.json").exists() else []
    corrections.sort(key=lambda c: c["date"], reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    if (ROOT / "wheel").exists():
        shutil.copytree(ROOT / "wheel", OUT / "wheel")
    if (ROOT / "CNAME").exists():
        shutil.copy(ROOT / "CNAME", OUT / "CNAME")
    (OUT / ".nojekyll").write_text("")

    latest = editions[0]
    write("index.html", page("", SITE_NAME, edition_body(latest, editions, is_home=True), latest.get("summary", ""), active=""))
    for ed in editions:
        write(f"{ed_url(ed['date'])}index.html",
              page(ed_url(ed["date"]), long_date(ed["date"]), edition_body(ed, editions), ed.get("summary", "")))

    # archive
    months = {}
    for ed in editions:
        months.setdefault(ed["date"][:7], []).append(ed)
    arch = ""
    for m, eds in months.items():
        label = pdate(m + "-01").strftime("%B %Y")
        items = "".join(
            f'<li><a href="{BASE}{ed_url(x["date"])}">{long_date(x["date"]).split(", ", 1)[1]}</a>'
            f'<span class="sum">{e(x.get("summary", ""))}</span><span class="n case">{len(x["entries"])}</span></li>' for x in eds)
        arch += f'<div class="month"><h3>{label}</h3><ul class="days">{items}</ul></div>'
    write("archive/index.html", page("archive/", "Archive",
          f'<main style="margin-top:28px"><h1 class="page">Archive</h1><p class="lede">Every daily edition, newest first. {len(editions)} editions.</p>{arch}</main>', active="archive/"))

    # open cases (from newest edition that has them)
    src = next((x for x in editions if x.get("open_cases")), None)
    cbody = render_cases(src["open_cases"], src["date"]) if src else "<p>No open cases tracked yet.</p>"
    write("cases/index.html", page("cases/", "Open cases",
          f'<main style="margin-top:28px"><h1 class="page">Open cases</h1><p class="lede">Felony and notable matters followed in Alaska CourtView, as of the {long_date(src["date"]) if src else ""} edition.</p>'
          f'<p class="presumption">Charged, not convicted, unless stated.</p>{cbody}</main>', active="cases/"))

    # corrections
    citems = "".join(
        f'<article class="entry"><div class="gutter"><span class="d">{short_date(c["date"])}</span><span>re: <a href="{BASE}{ed_url(c["edition"])}">{short_date(c["edition"])} edition</a></span></div>'
        f'<div><p>{e(c["text"])}</p></div></article>' for c in corrections) or "<p>No corrections yet.</p>"
    write("corrections/index.html", page("corrections/", "Corrections",
          f'<main style="margin-top:28px"><h1 class="page">Corrections</h1><p class="lede">Errors are corrected here rather than quietly edited away. Nothing on this page is ever removed.</p>{citems}</main>', active="corrections/"))

    # search
    index = []
    for ed in editions:
        for en in ed["entries"]:
            text = " ".join([en["title"], " ".join(en.get("body", [])), en.get("place", ""), en.get("agency", ""), " ".join(en.get("cases", []))])
            index.append({"date": short_date(en["date"]) + ", " + en["date"][:4], "agency": en.get("agency", ""), "title": en["title"],
                          "url": f'{ed_url(ed["date"])}#{en["id"]}', "snippet": (en.get("body") or [""])[0][:220],
                          "text": text.lower()})
    (OUT / "search-index.json").write_text(json.dumps(index, separators=(",", ":")))
    write("search/index.html", page("search/", "Search",
          '<main style="margin-top:28px"><h1 class="page">Search the record</h1><p class="lede">Search every edition by name, case number, place, charge or agency.</p>'
          '<input id="q" class="search-box" type="search" placeholder="e.g. burglary, 4FA-26-01446CR, North Pole" autocomplete="off" aria-label="Search">'
          '<div id="results" class="results"></div></main>', active="search/"))

    # about
    about = f"""<main style="margin-top:28px" class="prose"><h1 class="page">About this record</h1>
<p class="lede">A daily log of arrests, charges and court activity in Fairbanks and the surrounding Interior, compiled from primary public records each morning.</p>
<h2>Coverage</h2><p>Fairbanks, North Pole, Fort Wainwright, Eielson, Salcha, Delta Junction, Nenana, Minto, Anderson, Clear, Healy, Ester, Two Rivers and Moose Creek — roughly 100 miles around Fairbanks. Court filings are read for the Fairbanks (4FA), Nenana (4NE), Healy (4HE) and Delta Junction (4DJ) courts.</p>
<h2>Sources</h2><ul>
<li>Alaska State Troopers daily dispatch (D Detachment)</li><li>Fairbanks Police Department daily bulletin</li>
<li>Alaska Court System weekly charges and dispositions reports, and CourtView</li>
<li>Alaska Department of Law and U.S. Attorney, District of Alaska press releases</li><li>Local newsrooms</li></ul>
<h2>How to read it</h2>
<p>Police and trooper feeds add entries to past dates, sometimes days later. A count for any day is what had been posted at the time of reading, not a final total. Charge classes come from the court file where one exists; where only an arrest report exists, the charge is given as the arresting agency recorded it.</p>
<p>An arrest or charge is an accusation. Everyone named is presumed innocent unless and until proven guilty. Dates of birth are not published. Victims are not named. Domestic violence and child-related entries carry only what the court record states.</p>
<h2>Corrections and removal requests</h2><p>Errors are logged on the <a href="{BASE}corrections/">corrections page</a>. If a case was dismissed or you were acquitted, contact us with the case number and the entry will be updated to reflect the outcome.</p>
</main>"""
    write("about/index.html", page("about/", "About", about, active="about/"))

    write("404.html", page("404.html", "Not found", f'<main style="margin-top:28px"><h1 class="page">Page not found</h1><p><a href="{BASE}">Go to the latest edition</a></p></main>'))

    # RSS
    items = []
    for ed in editions[:30]:
        pub = dt.datetime.combine(pdate(ed["date"]), dt.time(13, 0), tzinfo=dt.timezone.utc)
        items.append(f"""<item><title>{e(long_date(ed['date']))}</title><link>{SITE_URL}{BASE}{ed_url(ed['date'])}</link>
<guid>{SITE_URL}{BASE}{ed_url(ed['date'])}</guid><pubDate>{format_datetime(pub)}</pubDate><description>{e(ed.get('summary', ''))}</description></item>""")
    (OUT / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}{BASE}</link>
<description>Daily crime and court record for Fairbanks and Interior Alaska.</description>{''.join(items)}</channel></rss>""")

    # sitemap
    urls = [""] + [ed_url(x["date"]) for x in editions] + ["archive/", "cases/", "corrections/", "about/", "search/", "wheel/"]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
                                     "".join(f"<url><loc>{SITE_URL}{BASE}{u}</loc></url>" for u in urls) + "</urlset>")
    print(f"Built {len(editions)} editions, {len(index)} entries -> {OUT}")


if __name__ == "__main__":
    build()
