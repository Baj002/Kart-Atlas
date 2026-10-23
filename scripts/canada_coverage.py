#!/usr/bin/env python3
"""Internal Canadian kart-calendar audit; no unsupported 'season unpublished' claims."""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba",
    "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia", "NT": "Northwest Territories",
    "NU": "Nunavut", "ON": "Ontario", "PE": "Prince Edward Island",
    "QC": "Quebec", "SK": "Saskatchewan", "YT": "Yukon",
}

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))

def build():
    races = load("site/events.json")["events"]
    organizers = load("data/organizers.json")["organizers"]
    sources = load("data/monitor_sources.json")["sources"]
    audit = load("reports/organizer_coverage.json")
    health = {o["organizer_id"]: o for o in audit.get("organizers", [])}
    upcoming = [e for e in races if e.get("country") == "Canada"
                and str(e.get("start", "")).startswith("2027")]
    entries = []
    for code, name in REGIONS.items():
        races_here = [e for e in upcoming if e.get("region") == code]
        orgs_here = [o for o in organizers if o.get("country") == "Canada"
                     and o.get("region") == code]
        sources_here = [s for s in sources if s.get("country") == "Canada"
                        and s.get("region") == code]
        official = sum(e.get("verification") == "Official" for e in races_here)
        secondary = sum(e.get("verification") == "Secondary" for e in races_here)
        if official:
            status = "official_2027_dates_indexed"
        elif races_here:
            status = "announced_2027_dates_need_primary_source"
        elif not sources_here:
            status = "no_verified_2027_dates_and_no_configured_regional_source"
        else:
            status = "no_2027_dates_verified_in_current_sources"
        entries.append({
            "code": code, "name": name, "status": status,
            "indexed_2027_races": len(races_here),
            "official_2027_races": official,
            "secondary_2027_races": secondary,
            "configured_regional_sources": [s["id"] for s in sources_here],
            "organizers": [
                {"id": o["id"], "name": o["name"],
                 "scope_status": o.get("scope_status", "needs_review"),
                 "season_2027": next((s["status"] for s in
                    health.get(o["id"], {}).get("seasons", [])
                    if s.get("year") == 2027), "not_audited")}
                for o in orgs_here
            ],
            "events": [{"id": e.get("id"), "start": e["start"],
                        "end": e.get("end"), "name": e["name"],
                        "verification": e.get("verification"),
                        "source": e.get("source")} for e in races_here]
        })
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "year": 2027, "scope": "Owner-kart competition circuit racing only",
        "regions_checked": len(REGIONS),
        "indexed_canadian_2027_events": len(upcoming),
        "status_meanings": {
            "no_2027_dates_verified_in_current_sources":
                "No 2027 event is verified in the configured sources; this does not prove an organizer has not published a schedule.",
            "no_verified_2027_dates_and_no_configured_regional_source":
                "No current source is configured for this region; do not infer there are no clubs or races.",
            "announced_2027_dates_need_primary_source":
                "Dates were reported but an official organizer event page has not been verified.",
            "official_2027_dates_indexed":
                "At least one 2027 event has an official organizer source; this does not mean the full season is covered."
        },
        "important": "Directory coverage is not a census. No verified dates never means no karting exists. Multi-region sources are audited separately.",
        "multi_region_sources": [s["id"] for s in sources if s.get("country") == "Canada"
                                 and s.get("region") == "Multi"],
        "regions": entries,
    }
    dest = ROOT / "reports/canada_2027.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Canada: {len(upcoming)} indexed 2027 races across {sum(bool(r['events']) for r in entries)} regions; {len(REGIONS)} regions audited.")
    return report

if __name__ == "__main__":
    build()
