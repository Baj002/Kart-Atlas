# Kart Atlas operations

Repository: https://github.com/Baj002/Kart-Atlas

## Automated refresh

The **Refresh North American kart calendar** GitHub Actions workflow validates code, scans public sources, rebuilds the static datasets, archives diagnostics, and commits valid updates. It runs daily at 13:17 UTC, on relevant main-branch changes, and via **Actions → Run workflow**. Pull requests run offline tests only. The refresh job needs `contents: write`; it does not send messages or create daily issues.

Generated outputs:

- `data/automated_events.json`: persisted events and lifecycle history.
- `data/discovered_sources.json`: discovered websites and rotation timestamps.
- `reports/discovery.json`: per-page results, changes, race candidates, newly found feeds/websites, and errors.
- `reports/coverage.json` and `site/coverage.json`: measured source reach and coverage gaps.
- `site/events.json`, `site/clubs.json`, `site/monitor_status.json`: app datasets.

A successful workflow does not mean every source succeeded. Inspect `/coverage.html` or the archived `discovery-report` artifact for failures and scan-limit deferrals. The final live health check fails if no trusted source was reached. Failed fetches never delete or cancel races.

## Source maintenance

1. Check new website leads in `data/discovered_sources.json` against the actual organizer website and its current location. Historical directory links can expire or change ownership.
2. Add verified organizer sources to `data/monitor_sources.json` with a unique ID, URL, organizer name, venue, city, region and country. Specify an IANA timezone for ICS feeds with UTC timestamps (for example `America/Vancouver` for WCKC). Multi-venue series need event-specific locations.
3. Set legacy `mode: watch` and `auto_import: false` for HTML sources. Production discovery uses structured data from verified sources regardless of that legacy field.
4. Add a regression fixture for each new parser or changed behavior. Run the commands in README before publishing.
5. Set `pdf_profile` only after checking the actual schedule layout and excluded reserve dates. The `date_columns` profile is appropriate for Norwalk’s reviewed two-column date-only schedule. Use a stable `event_namespace` when the same schedule is available at multiple or revised URLs. Without a reviewed profile, PDF event rows remain candidates.
6. `table_events` and `feed_events` can map verified organizer labels to an existing `curated_id`, preserving saved-race IDs when dates change. Use `table_mapping_window` / `feed_mapping_window` to limit saved-race mappings to the reviewed season; recurring round labels must never move a previous season’s saved race into the next season. Update mappings if curated event identities change. Public RaceSelect cards remain review-only by default; registration disabled does not mean race cancelled.
7. Curated corrections belong in `data/races.csv`. A workflow run rebuilds those into the app. The curated snapshot date is retained separately from the generated dataset date.

Five pages per source are scanned by default. `data/discovery_sources.json` controls this and the rotating new-website batch size. Requests obey robots.txt, serialize by host and honor crawl delays. Text-layer PDFs can be scanned with the pinned `pypdf` dependency; image-only schedules and sources behind access restrictions remain explicit gaps. A PDF font/layout failure cannot stop unrelated organizer scans and never enables automatic plain-text publishing. Review candidates are not silently published with guessed dates or locations.

## Hosting

For Git-integrated Cloudflare Pages, production branch is `main`, output directory is `site`, framework is None, and the build command can be blank: GitHub Actions commits prebuilt datasets. A Cloudflare Worker using static assets must likewise serve the repository's `site` directory. Keep the existing stable public origin when updating an installed PWA.

Hosting account configuration and the deployed public origin are not stored in this repository. Verify the provider deployment status and the live site's `events.json`/`coverage.json` after connecting Git integration. A GitHub commit alone does not prove a Cloudflare deployment succeeded.

## Installed app updates

The service worker fetches same-origin resources from the network first and falls back to its cache when offline. Content changes should appear when the app reconnects; users do not need to reinstall for ordinary dataset changes. A change to a different domain/origin is a distinct app installation.

## External platform access

MotorsportReg's aggregate API requires prior provider approval, authentication and attribution under its published documentation: https://api.motorsportreg.com/. Provider approval is separate from GitHub access and is not represented as enabled by this project. Do not put credentials in the public repository. A future approved integration should use GitHub Actions secrets and public event/calendar resources only, without entrant data.
