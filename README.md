# Kart Atlas — public North American kart racing calendar

**Zero-monthly-fee architecture:** static PWA on Cloudflare Pages + public GitHub repo + standard GitHub-hosted Actions. No paid APIs, subscription, database or domain required for the starter version. Free-tier/service policies may change.

**Status at delivery:** GitHub and Cloudflare accounts have *not* been connected or deployed. The source-monitoring code is built and offline-tested, but it cannot be proven operational against each live organizer source until the first GitHub Actions run. This archive is not a live website by itself.

## What is included

- `site/` — installable mobile-friendly calendar; race search and filters, favorites and `.ics` downloads.
- `site/clubs.html` — searchable directory of **132 research leads** (only **16** currently cross-referenced to watched sources). Leads **are not** all verified active clubs.
- `data/races.csv` — manually curated source snapshot, **97 initial races**.
- `data/monitor_sources.json` — **20 named organizer source pages**, two candidate public ICS feeds for automatic additions; 18 ordinary websites are **change watch only**.
- `scripts/check_sources.py` — daily polite monitor. Follows robots.txt, uses standard HTTP, limits response size and time, reports failures without altering race dates. No paywall or captcha bypass.
- `data/automated_events.json` — validated feed race additions (starts empty).
- `scripts/build_site.py` — merges curated data and automated feed events, deduplicates where possible, publishes `site/events.json` and `site/clubs.json`.
- `.github/workflows/refresh-kart-calendar.yml` — daily checks, rebuild, local unit tests, commit and automatic Cloudflare redeploy. Opens GitHub issues when an organizer schedule changes and needs review.
- `.github/ISSUE_TEMPLATE/` — free community race/club submission forms through GitHub (users need free GitHub accounts).
- `tests/` — six offline tests for calendar parsing, duplicate handling, change detection, blocked sources and failures.

## Publish (public, free)

See [DEPLOY_AND_MAINTAIN.md](DEPLOY_AND_MAINTAIN.md) for the exact steps. **Use Cloudflare Pages' Git integration**, not its old direct-upload flow, to keep future updates automatic. Cloudflare build output directory: `site`. Framework: None. Build command: blank or `exit 0`. Production branch: `main`.

## How automation behaves

| Data source | Daily behavior | Date changes shown automatically? |
|---|---|---|
| Official ICS organizer exports | Imports future race-like events; excludes practice, private events, arrive-and-drive, cancelled/recurring records; labels as **Organizer feed · unreviewed** | **New qualifying events: yes.** Changes to existing events: flagged for review, not silently overwritten. |
| Official HTML club schedules | Text content fingerprint watched, changes open review issues | No; schedule pages vary too much to infer race dates safely. |
| PDFs, social media, login-only platforms | Directory/research lead only, no circumventing restrictions | No; human review or a supported feed required. |
| Curated organizer-verified events in CSV | Retained as researched snapshot | Manual corrections are authoritative and not overwritten by automated collection. |

**Do not represent the calendar as exhaustive or race dates as guaranteed.** 2027 grassroots club seasons may not yet be published. A source monitor can fail due to robots rules, organizer changes, rate limits or provider availability. The app displays number of sources reached after a scheduled run. The original 97 listings remain based on October 16, 2026 research until reviewed.

## Local QA (no internet needed)

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
python3 -m http.server 8000 --directory site
```

Open `http://localhost:8000`. Running `python3 scripts/check_sources.py` requires outbound internet and will write `data/source_state.json`, `reports/latest.json`, `site/monitor_status.json` and possibly `data/automated_events.json`.

## Responsible community submissions

Click the GitHub **Issues > New issue** form after the public repo is created. Require a race organizer source URL, reject practice/rental-only events and duplicates, and verify changes or cancellations before updating `data/races.csv`. Avoid collecting entrant personal information.

## References

- Cloudflare Pages Git integration: https://developers.cloudflare.com/pages/get-started/git-integration/
- GitHub Actions billing: https://docs.github.com/en/actions/concepts/billing-and-usage
- GitHub scheduled workflows: https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule
- Official schedule sources are listed with exact URLs in `data/monitor_sources.json`.
