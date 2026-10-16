#!/usr/bin/env python3
"""Print, as JSON, every court case number this site covered this week (Monday to the given day).
Usage: python3 scripts/bail_week_cases.py [YYYY-MM-DD]   (default: yesterday in Alaska — the nightly run covers editions through yesterday)"""
import json, re, sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
ED = Path(__file__).resolve().parent.parent / "data" / "editions"
day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(ZoneInfo("America/Anchorage")).date() - dt.timedelta(days=1)
mon = day - dt.timedelta(days=day.weekday())
cases = set()
for i in range((day - mon).days + 1):
    f = ED / f"{(mon + dt.timedelta(days=i)).isoformat()}.json"
    if f.exists():
        cases |= set(re.findall(r"4(?:FA|NE|HE|DJ)-\d\d-\d{5}CR", f.read_text()))
print(json.dumps({"date": day.isoformat(), "week_start": mon.isoformat(), "cases": sorted(cases)}))
