# dickwheel.com — public website

Static site built from one JSON file per day. The daily 5am Claude scheduled task does the research and drops
`edition-YYYY-MM-DD.json` into the public Google Drive folder "dickwheel feed".
Every hour, the "Pull new editions from Google Drive" GitHub Action copies any new
file into `data/editions/`, rebuilds the site and deploys it to GitHub Pages.
Any push to main also rebuilds.

```
data/editions/2026-09-27.json   one file per day (the record)
data/corrections.json           append-only corrections log
build.py                        generator, no dependencies  ->  public/
static/                         CSS + JS
scripts/import_drive.py         pulls new editions from the Drive folder
.github/workflows/deploy.yml    build + deploy on push
.github/workflows/sync-from-drive.yml   hourly Drive pull -> commit -> deploy
CNAME                           your domain (create when you have one)
```

## Pages generated
Home (latest edition) · `/editions/YYYY-MM-DD/` for every day · Archive · Open cases ·
Search (client-side, all editions) · Corrections · About · RSS `/feed.xml` · sitemap.

## One-time setup
1. Upload these files to the GitHub repo planetsurplus/dickwheel (include the hidden `.github` folder).
2. Repo → Settings → Pages → Source: **GitHub Actions**; Custom domain: `dickwheel.com`; Enforce HTTPS.
3. DNS at the registrar: A records for @ → 185.199.108.153 / .109.153 / .110.153 / .111.153; CNAME www → planetsurplus.github.io.
4. Google Drive: folder **dickwheel feed** → Share → General access: **Anyone with the link — Viewer**.
5. Repo → Actions → "Pull new editions from Google Drive" → **Run workflow** once to test.

## Edition JSON format
```jsonc
{
  "date": "2026-09-28",              // must match file name
  "compiled": "05:40 AKDT",
  "window": "Sep. 26–28, 2026",
  "summary": "One or two plain sentences on the day's main items.",
  "commentary": null,                // or {"title": "...", "body": ["para", "para"]} -> side column
  "entries": [{
    "id": "short-slug",              // unique within the edition
    "date": "2026-09-27",            // incident / filing date
    "time": "20:10",                 // optional
    "place": "North Pole",
    "agency": "Alaska State Troopers",
    "category": "violent | property | dui | drug | court | other",
    "severity": "felony | misdemeanor | other",
    "cases": ["4FA-26-01933CR"],
    "title": "Plain factual headline",
    "body": ["Paragraph.", "Paragraph."],
    "tags": [],                      // optional extra chips
    "sources": [{"label": "AST daily dispatch, Sep. 27", "url": "https://..."}]
  }],
  "filings": {"window": "...", "courts": [{"court": "Fairbanks (4FA)", "count": 61}],
              "new": [{"case": "...", "defendant": "Last, First", "charges": "...", "felony": true}]},
  "open_cases": [{"case": "...", "defendant": "...", "level": "Class B felony", "charges": "...",
                  "next": "...", "judge": "...", "last_docket": "2026-09-25"}],
  "sources": [{"name": "...", "url": "...", "status": "read | stale | not reached", "note": "..."}]
}
```

## Public-site rules (straight tone)
- Plain factual language. No jokes or opinion in entries — opinion goes only in `commentary`.
- No dates of birth. No victim names. DV/child entries: only what the court record states.
- Everyone is "arrested" or "charged", never implied guilty.
- Corrections are appended to `corrections.json`, never deleted.

## Local preview
`python3 build.py && python3 -m http.server -d public 8000` → http://localhost:8000
