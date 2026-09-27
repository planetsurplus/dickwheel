#!/usr/bin/env python3
"""Pull daily edition files from the public Google Drive folder into data/.

The 5am Claude task drops one file per day into the Drive folder, named
    edition-YYYY-MM-DD.json        (or edition-YYYY-MM-DD-r2.json for a re-run; highest rN wins)
Each file is an edition (see README) plus an optional "corrections" list.

Env: DRIVE_FOLDER_ID (required), LOOKBACK_DAYS (default 21)
Exit 0 always on "nothing new"; exit 1 on errors so the workflow shows red.
"""
import json, os, re, sys, datetime as dt, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ED_DIR = ROOT / "data" / "editions"
CORR = ROOT / "data" / "corrections.json"
FOLDER = os.environ.get("DRIVE_FOLDER_ID") or sys.exit("DRIVE_FOLDER_ID not set")
LOOKBACK = int(os.environ.get("LOOKBACK_DAYS", "21"))
UA = {"User-Agent": "Mozilla/5.0 (dickwheel.com site builder)"}
NAME_RE = re.compile(r"^edition-(\d{4}-\d{2}-\d{2})(?:-r(\d+))?\.json$")


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def list_folder(html):
    """Return [(file_id, title)] from Drive's embedded folder view."""
    out = re.findall(r'id="entry-([\w-]{10,})".*?class="flip-entry-title">([^<]+)<', html, re.S)
    return [(fid, t.strip()) for fid, t in out]


def download(fid):
    for url in (f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",
                f"https://drive.google.com/uc?export=download&id={fid}"):
        try:
            return json.loads(get(url).decode("utf-8"))
        except Exception as err:
            last = err
    raise RuntimeError(f"could not download {fid}: {last}")


def validate(ed, date):
    if ed.get("date") != date:
        raise ValueError(f"file says date {ed.get('date')}, name says {date}")
    if not isinstance(ed.get("entries"), list):
        raise ValueError("missing entries list")
    ids = [e.get("id") for e in ed["entries"]]
    if len(ids) != len(set(ids)) or not all(ids):
        raise ValueError("entry ids missing or duplicated")
    for e in ed["entries"]:
        for k in ("title", "date", "body"):
            if k not in e:
                raise ValueError(f"entry {e.get('id')} missing {k}")


def main(html=None):
    html = html or get(f"https://drive.google.com/embeddedfolderview?id={FOLDER}").decode("utf-8", "replace")
    files = list_folder(html)
    if not files:
        sys.exit("ERROR: no files found in Drive folder — is it shared 'Anyone with the link'?")
    cutoff = (dt.date.today() - dt.timedelta(days=LOOKBACK)).isoformat()
    best = {}  # date -> (rev, id)
    for fid, title in files:
        m = NAME_RE.match(title)
        if m and m.group(1) >= cutoff:
            rev = int(m.group(2) or 1)
            if rev >= best.get(m.group(1), (0, ""))[0]:
                best[m.group(1)] = (rev, fid)
    corrections = json.loads(CORR.read_text()) if CORR.exists() else []
    seen = {(c["date"], c["text"]) for c in corrections}
    changed, errors = [], []
    for date, (rev, fid) in sorted(best.items()):
        try:
            ed = download(fid)
            validate(ed, date)
        except Exception as err:
            errors.append(f"{date}: {err}")
            continue
        for c in ed.pop("corrections", None) or []:           # append-only merge
            if {"date", "edition", "text"} <= c.keys() and (c["date"], c["text"]) not in seen:
                corrections.append(c); seen.add((c["date"], c["text"])); changed.append(f"correction {c['date']}")
        path = ED_DIR / f"{date}.json"
        new = json.dumps(ed, ensure_ascii=False, indent=2) + "\n"
        if not path.exists() or path.read_text() != new:
            path.write_text(new); changed.append(date)
    if changed:
        corrections.sort(key=lambda c: c["date"], reverse=True)
        CORR.write_text(json.dumps(corrections, ensure_ascii=False, indent=2) + "\n")
    print("Updated:", ", ".join(changed) if changed else "nothing new")
    if errors:
        print("ERRORS:\n  " + "\n  ".join(errors)); sys.exit(1)


if __name__ == "__main__":
    main()
