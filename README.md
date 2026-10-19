# Kart Atlas

Public, installable North American kart racing calendar for Canada, USA and Mexico. Static site in `site/`, standard-library Python discovery pipeline, and daily GitHub Actions refresh. No paid API is required for the implemented adapters.

## Discovery and publication

`python -m scripts.discover_events` scans configured organizer sources, distinct directory websites, federation/industry directories, and a rotating batch of previously discovered websites. Each source has a bounded crawl (default five pages), following same-domain calendar/event links. Sources on different hosts are scanned concurrently; requests on each host are serialized, rate limited and checked against robots.txt. Retrieval errors preserve published data.

Supported data:

- Schema.org Event/SportsEvent JSON-LD, including nested lists and graphs, explicit dates, venues and cancellation/postponement status.
- HTML schedule tables with explicit date/year context; offsite rounds are deferred for location review.
- Squarespace event listing cards with machine-readable dates and registration links, including WCKC.
- Public ICS exports, including linked `.ics`, `?ical=1`, and Squarespace `?format=ical` calendars. Exclusive all-day end dates are converted to inclusive race dates. Recurring events/exceptions require review.
- English, French and Spanish race terms. Practice, rental sessions, meetings and other non-racing records are filtered.

Configured organizer sources in `data/monitor_sources.json` are trusted publication origins. A future race with a specific location can be automatically added. New websites discovered through directories are scanned as **unverified leads**, and their events stay in `reports/discovery.json` until the source is verified. A directory link alone is not proof that a historical club is active or that an expired domain still belongs to it.

Stable event identities retain first/last observations and a bounded change history. Explicit organizer date changes, cancellations and postponements update automated events. An event disappearing from a page is **not** treated as cancelled. Curated CSV records keep their saved-race IDs; automatic lifecycle updates apply only when the specific organizer event URL matches. Curated metadata otherwise takes precedence.

`python -m scripts.build_site` merges curated and automated races. `python -m scripts.coverage_report` writes public coverage metrics and per-source failures. The app's **Discovery coverage** page shows source reach, upcoming races by country/region, unmonitored directory entries, candidates and scan-budget deferrals. These measurements are not a claim to have found every race.

## Run and test

From the repository root, with Python 3.12 (no third-party runtime dependencies):

```bash
python -m unittest discover -s tests -v
python -m scripts.discover_events
python -m scripts.build_site
python -m scripts.coverage_report
python -m scripts.validate_data --live
python -m http.server 8000 --directory site
```

Offline tests exercise parsing, multilingual filtering, duplicate isolation, rescheduling, cancellations/reinstatement, failed-source retention, robots refusal, crawl limits and an end-to-end fixture refresh. `validate_data` blocks malformed dates, URLs, IDs and unsupported countries from publication. The live health gate fails when no trusted source was reached or the report is stale.

## Automation and deployment

`.github/workflows/refresh-kart-calendar.yml` runs daily at 13:17 UTC, on relevant changes to main, or manually. Pull requests run offline validation only. Refreshes discover first, build second, validate, archive diagnostics and commit generated data; they never post routine messages or open daily review issues. GitHub schedule timing is approximate. See [deployment notes](DEPLOY_AND_MAINTAIN.md).

The service worker uses network-first retrieval so installed apps pick up new data when connected. Moving to a different origin remains a separate installation; a stable hosting address matters.

## Coverage boundaries and next adapters

There is no reliable denominator for all North American races. Many schedules are images/PDFs, custom HTML tables, social-only announcements, or behind login. Linked PDFs are recorded for review. Unknown dates, missing venues and uncertain locations are not guessed. Research-directory entries are leads, not verified active clubs.

MotorsportReg's aggregate calendar API requires provider approval and credentials, even though some organization calendars are unauthenticated. Its [official documentation](https://api.motorsportreg.com/) also requires attribution. This project does not call that API without approval. Public MotorsportReg pages linked by configured organizers can be discovered, but that does not provide platform-wide API coverage. `scripts/enrich_motorsportreg.py` is a legacy optional enrichment utility, not the production refresh path.

Legacy `check_sources.py` remains available for text fingerprints and ICS regression compatibility. The production refresh uses `discovery_engine.py` so monitoring and publication share a single scan and provenance model.
