# Kart Atlas — U.S. 50-state coverage audit, November 11, 2026

**Status: INCOMPLETE.** This is an incremental verified organizer-schedule pass. It is **not** a completed comprehensive available-schedules audit of all 50 states.

## Confirmed repository changes

- Added **nine historical 2026 Montana Karting Association owner-kart sprint races** to both `data/races.csv` and `site/events.json`, creating the first Montana race listings.
- Exact race dates: **May 30, May 31, June 13, June 14, July 18, August 29, September 26, September 27 and October 3, 2026**. All nine are distinct organizer-published single-day races, not nine inferred rounds or practice days.
- Venue: **Rocky Mountain Emergency Services Training Center Road Course, 3425 Skyway Drive, Helena, MT**. Organizer confirms this is paved sprint-kart racing.
- Official race calendar: https://montanakarting.com/race-dates/ ; organizer-created MotorsportReg event index: https://www.motorsportreg.com/venues/montana-karting-association-helena-mt . Each new record includes its own MotorsportReg event page.
- Added **three watch-only official sources**, with corresponding organizer bindings:
  - Montana Karting Association (MT): https://montanakarting.com/race-dates/ . Monitor for 2027 dates.
  - Maui Go Karters Association (HI): https://mauigokart.com/ . SKUSA-sanctioned sprint course; three future race rounds explicitly **TBD**. **No Hawaii races published**.
  - Hampton Roads Kart Club (VA): https://www.hrkc.com/schedule/ . Club runs both oval and road-course karting; page is labeled **2025**, so **no 2026/2027 Virginia races published** without updated official race-day/format verification.
- Montana's existing directory organizer was upgraded rather than duplicated. Virginia's existing organizer was bound to the official source; Maui was newly registered.
- All new monitor entries are `mode: watch`, `auto_import: false`, so unpublished dates cannot be silently imported.

## Repository snapshot (November 11)

| Metric | Verified count |
| --- | ---: |
| Total North American indexed events | **393** |
| U.S. indexed events | **240** |
| U.S. states with race listings | **31 / 50** |
| U.S. events on or after Nov 11, 2026 | **100** |
| U.S. state-specific monitored-source coverage | **38 / 50** |
| U.S. monitoring source entries | **63** |
| All monitoring entries | **108** |
| Source entries without exactly one organizer binding | **0** |
| Duplicate event IDs in site/events.json | **0** |
| Montana race rows in both CSV and JSON | **9 / 9** |

The initial repository snapshot before this pass already had **384** events, including five records added through existing imports after the November 10 audit; the nine curated Montana additions brought the total to 393.

## States without state-specific monitored official sources

**AL, AK, DE, KY, ME, MA, MN, NM, ND, RI, SD, WY** (12 states).

Other states with monitored sources may still lack verified published race dates. **Hawaii and Virginia have monitoring entries but no eligible published race records.** A source entry measures a known official organizer page, not complete schedule coverage.

## Quality safeguards and blockers

- The nine Montana race dates and the Helena venue are independently supported by the organizer's own published calendar and its MotorsportReg registration listings.
- No 2027 race dates were fabricated from 2026 schedules. No practice, time-attack, oval, rental or vintage kart events were added.
- The event feed and curated CSV were updated in the repository, and the build script's curated snapshot was advanced to November 11. The post-write integrity review found **no duplicate event IDs**, nine matching Montana entries in both files, and **all 108 monitoring entries bound to exactly one organizer**.
- Full repository CI/test execution and the Cloudflare production deployment were **not independently confirmed**.

**The comprehensive available-schedules pass across all 50 U.S. states is NOT FINISHED.** Continue researching the 12 remaining source gaps, monitoring publication of 2027 official calendars, and verifying event-level eligibility before import.
