# Kart Atlas

Public, installable North American kart racing calendar for Canada, USA and Mexico. Static site in `site/`, Python discovery pipeline, and daily GitHub Actions refresh. No paid API is required for the implemented adapters. The runtime dependency is pinned in `requirements.txt`.

Scope is competition circuit karting: Briggs LO206, Rotax, ROK, shifter, IAME/KA100 and comparable classes. The conventional `Sprint` label means this circuit karting. Oval, dirt, vintage, long-circuit road-racing programs, rental leagues and other motorsports are excluded. Missing engine/class details never exclude an otherwise eligible race. Owner-kart endurance events remain eligible; concession-kart enduros do not.

`data/racing_scope.json` records reviewed exclusions and event corrections with evidence. The same scope checks apply to HTML/JSON-LD, ICS feeds, retained automated events, curated publication and final validation. `reports/scope_audit.json` records exclusions without rewriting historical CSV IDs. Daytona KartWeek's circuit races are explicitly separated from its dirt/road programs and retain the original saved-race ID.

## Internal registry and health

`data/organizers.json` holds stable organizer IDs, explicit aliases, source bindings, scope verification and evidence-backed season declarations. `reports/organizer_coverage.json` distinguishes future indexed races, past-only listings, missing sources, inaccessible sources, unverified dates and reviewed season completion/non-announcement. A directory lead is not a verified active club. Non-announcement declarations expire after seven days, and future indexed dates supersede older declarations. Cached listings without recent verification are marked for review.

Discovery persists per-source health in `data/source_state.json`: last success, failure streak, bounded scan history and expected future event identities. Empty or reduced schedules are flagged when known future events disappear; explicit cancellations and completed dates do not generate false missing-event alarms. Fetch failures never cancel retained races. Evidence-backed duplicate identities in `data/racing_scope.json` preserve former saved IDs as aliases, including copies with unannounced venues. Health and organizer audits stay in repository reports and workflow artifacts, not new public app pages.

## Discovery and publication

`python -m scripts.discover_events` scans configured organizer sources, distinct directory websites, federation/industry directories, and a rotating batch of previously discovered websites. Each source has a bounded crawl (default five pages), following same-domain calendar/event links. Roots are checked daily; unseen and least-recently-attempted linked pages rotate ahead of previously checked pages so scan limits do not permanently starve deeper links. Sources on different hosts are scanned concurrently; requests on each host are serialized, rate limited and checked against robots.txt. Retrieval errors preserve published data.

Supported data:

- Schema.org Event/SportsEvent JSON-LD, including nested lists and graphs, explicit dates, venues and cancellation/postponement status.
- HTML schedule tables with explicit date/year context, including reordered date columns. Reviewed row mappings connect PKRA rounds to existing saved-race IDs; offsite rounds are deferred for location review.
- Bounded text-layer PDF schedules. A reviewed layout profile enables automatic import (including Norwalk’s two-column schedule); unprofiled rows, image-only documents and font-layout fallbacks remain review-only. Rain, reserve, practice and tentative dates are excluded.
- Public RaceSelect calendar cards expose explicit date ranges and registration status. They remain review-only until event location is verified; private event details are never accessed.
- Reviewed text sections support custom organizer schedules with explicit year headings and section boundaries. Multi-venue rounds require verified venue mappings; unknown tracks and tentative schedules stay in review. Tri-C's 2027 calendar and Monterrey's kart championship use this adapter. SKUSA and ROK Sonoma announcements use explicit round identities and season-specific saved-race mappings, so rescheduled dates update existing listings. Unannounced tracks remain review candidates. Mosport's public CMS calendar is parsed from reviewed data attributes, with owner-race categories isolated from rental leagues and practice.
- Shared series URLs do not collapse distinct JSON-LD rounds. Squarespace multi-day cards retain end dates and use reviewed venue aliases for travelling clubs.
- Labelled Joomla `.raw` calendar exports, with organizer-specific title/description rules for NTK.
- Squarespace event listing cards with machine-readable dates and registration links, including WCKC.
- Public ICS exports, including linked `.ics`, `?ical=1`, and Squarespace `?format=ical` calendars. Exclusive all-day end dates are converted to inclusive race dates. Recurring events/exceptions require review.
- English, French and Spanish race terms. Practice, rental sessions, meetings and other non-racing records are filtered.

Configured organizer sources in `data/monitor_sources.json` are trusted publication origins. A future race with a specific location can be automatically added. New websites discovered through directories are scanned as **unverified leads**, and their events stay in `reports/discovery.json` until the source is verified. A directory link alone is not proof that a historical club is active or that an expired domain still belongs to it.

Stable event identities retain first/last observations and a bounded change history. Explicit organizer date changes, cancellations and postponements update automated events. An event disappearing from a page is **not** treated as cancelled. Curated CSV records keep their saved-race IDs; automatic lifecycle updates apply only when the specific organizer event URL matches. Curated metadata otherwise takes precedence.

Punctuation-only curated copies merge only when the dates, venue, country, region and exact official source agree. Former IDs remain `alias_ids`, so users can still find and remove those races from their saved list. Different events at the same venue are retained.

`python -m scripts.build_site` merges curated and automated races. `python -m scripts.coverage_report` writes diagnostic metrics and per-source failures to `reports/coverage.json`. Inspect the workflow's archived discovery report for regional gaps, date conflicts, review candidates, PDF extraction counts and scan-budget deferrals. The internal dashboard is not a deployed app page. Image/gallery URLs are excluded from the organizer lead inventory and retained in its rejection audit. These measurements are not a claim to have found every race.

## Run and test

From the repository root, with Python 3.12 and the pinned PDF text parser:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
node tests/test_coverage_ui.js
node tests/test_saved_aliases.js
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

There is no reliable denominator for all North American races. Many schedules are images/PDFs, custom HTML tables, social-only announcements, or behind login. Linked schedule PDFs can be read within the same crawl budget. Generic documents remain review-only unless their layout profile has been verified. Image-only schedules are reported for OCR/manual review; no OCR dates are automatically published. Unknown dates, missing venues and uncertain locations are not guessed. Research-directory entries are leads, not verified active clubs.

MotorsportReg's aggregate calendar API requires provider approval and credentials, even though some organization calendars are unauthenticated. Its [official documentation](https://api.motorsportreg.com/) also requires attribution. This project does not call that API without approval. Public MotorsportReg pages linked by configured organizers can be discovered, but that does not provide platform-wide API coverage. `scripts/enrich_motorsportreg.py` is a legacy optional enrichment utility, not the production refresh path.

Legacy `check_sources.py` remains available for text fingerprints and ICS regression compatibility. The production refresh uses `discovery_engine.py` so monitoring and publication share a single scan and provenance model.


## Registration links and deadlines

Race cards, event details, calendar exports and printable overviews now show registration information. A registration link alone never means entries are open. The browser computes **Closing soon** within seven days of a verified online deadline, and marks a published deadline as passed at its exact instant. Times are displayed in the user's time zone. Cancelled, postponed and completed events cannot display an open-entry badge.

Explicit open/closed/sold-out status checks expire after 48 hours, including offline. Stale information becomes **Check status**; missing information is **Not announced** (no verified announcement indexed yet). Early-entry pricing cutoffs and class-specific capacity can differ from the provider's online-entry deadline.

`data/registration_sources.json` binds reviewed public platform rows to stable event IDs. `python -m scripts.registration` refreshes `data/event_registration.json`; the daily workflow runs it before building the site. A failed request or missing event row retains the prior observation without renewing its timestamp. Featured and compact RaceSelect rows are isolated so membership deadlines cannot leak into race entries. Add a reviewed event ID, exact platform event URL and public list URL to expand coverage. No login or private API is required.


## Saved-race deadline reminders

**Manage reminders** tracks all saved races, independently of search filters. Users can enable in-app reminders, choose 1 hour / 1 day / 3 days / 1 week, and exclude individual races. Unknown deadlines stay in a waiting state; cancelled, postponed, closed and sold-out events do not trigger reminders. Race aliases preserve saved selections. Visible pages check the reminder window every minute and refresh published race data at most every 15 minutes; a manual refresh is also available. Failed fetches retain the loaded data and never renew registration verification timestamps.

For alerts after Kart Atlas closes, users can download saved deadlines as an iCalendar file with display alarms. Downloads are snapshots, and must be replaced or removed in the calendar when dates or saved selections change. Already-passed lead-time alarms are omitted; an alarm at the deadline remains. Calendar applications control import behavior, permissions and alert delivery, so users should confirm their calendar's alert settings.

Each upcoming race also gets a stable public calendar subscription at `/reminders/<race-id>.ics`. Races without a verified deadline have an empty subscription; an event appears when a deadline is verified. The build updates subscribed deadlines, retains old alias subscription URLs, and publishes cancellation records without alarms when an event is cancelled, postponed, removed, or its deadline becomes unavailable. Subscriptions use 1-day, 1-hour and deadline alarms, independently of the user's downloaded-calendar lead time. Subscription refresh timing is controlled by the calendar application. In-app opt-outs do not unsubscribe external calendars. The static subscription feeds contain only public race information; no saved-race lists are uploaded.

This web version does **not** promise scheduled push notifications while closed. No notification permission prompt or server push service is introduced. Native/push delivery can be added separately during mobile app development.


## Android and iPhone release preparation

The native release project uses pinned Capacitor packages and reproducibly generates Android and iOS projects. See `mobile/RELEASE.md` for build commands, unsigned CI artifacts, native reminder behavior, privacy/store drafts and the owner-confirmed submission gate. `npm run mobile:prepare` bundles public assets and an offline directory; `npm run mobile:sync` creates and synchronizes the native projects. Store publication is not automated.

## Website push reminders

Optional background registration alerts are implemented for compatible browsers and Home Screen web apps. The private Cloudflare delivery backend needs one-time owner activation before alerts can be sent. See [push/README.md](push/README.md) for setup, privacy, limits and device acceptance checks.
