# Kart Atlas — U.S. 50-state coverage audit, November 14, 2026

**Status: INCOMPLETE.** This was a targeted official-source review and data-quality update, **not** a completed comprehensive available-schedules pass across all 50 states.

## Verified new race listings

Two **2027 Race Rotax USA RMC Winter Trophy weekends** were verified from the organizer's October 8, 2026 season announcement and event schedule, both at **Orlando Kart Center, Orlando, Florida**:

| Race weekend | Dates | Published venue | Canonical event ID |
| --- | --- | --- | --- |
| RMC Winter Trophy 2027 Rounds 1 & 2 | January 22–24, 2027 | Orlando Kart Center | `9d51b4cf0d38` |
| RMC Winter Trophy 2027 Rounds 3 & 4 | February 19–21, 2027 | Orlando Kart Center | `cf8994cf05e9` |

Official organizer sources:
- https://www.racerotax.com/2027-rmc-season-update-winter-trophy-location-grand-finals-tickets-and-prizes
- https://www.racerotax.com/events/rmc-winter-trophy-event-schedule-2027
- https://www.racerotax.com/events/rmc-winter-trophy-faq-2027

Each weekend is **one race listing** containing two championship rounds, avoiding double-counting. The RMC America's Trophy weekends (April 16–18 and June 18–20) and RMC US Trophy Final (July 30–August 1) have **unannounced venues** in the organizer announcement; no location was inferred or published for those events.

## Monitoring additions

Two official watch-only sources were registered with distinct organizer bindings:
- `race-rotax-usa-2027`: Race Rotax USA's official 2027 season announcement (FL).
- `stars-championship-2027`: https://www.starschampionshipseries.com/ (multistate). The 2027 schedule is published as an image; exact dates and venues were not extracted from a secondary team calendar or guessed. Continue monitoring the official image and event announcements.

Both new monitoring sources have `auto_import: false`.

## Further state-gap screening

The remaining state-specific source gaps remain **AL, AK, DE, KY, ME, MA, NM, ND, RI, SD and WY**. No qualifying official 2027 owner-kart sprint schedule with verified dates and venue was added from these states in this pass.

Specific exclusions and unresolved candidates:
- **ND:** Red River Kart Club's official site reports 2027 uncertainty after its land was sold. Its 1/10-mile track is an **asphalt oval**, outside the sprint-circuit scope. https://www.redriverkartclub.com/ and https://redriverkartclub.com/blog/?p=4247
- **ME:** Boxshop Karting Club/Shredway Maine's official homepage currently advertises the facility for sale. Historic kart activities are visible, but no current eligible owner-kart sprint championship schedule is confirmed: https://boxshopkarting.club/
- **AL:** Talladega Gran Prix Raceway advertises open kart track days, not a verified kart race championship: https://www.motorsportreg.com/orgs/talladega-gran-prix-raceway
- **NM:** Suika Circuit's 2026 Super Cup includes shifter karts but uses a 1.7-mile car road course; this is outside the app's short sprint-circuit scope: https://www.motorsportreg.com/events/super-cup-race-1-suika-circuit-albuquerque-390609
- **MA:** Seaside Le Mans is a supplied-kart charity endurance event, not the eligible owner-kart sprint format: https://seasidelemans.org/
- **KY:** NCM Kartplex calendar lists facility opening and rental activities, not a confirmed owner-kart sprint championship: https://www.motorsportspark.org/event-calendar/

The absence of qualifying records is **not** a claim that no kart racing exists in those states.

## Post-write integrity

| Metric | Verified |
| --- | ---: |
| Total indexed North American races | **431** |
| U.S. race records | **278** |
| U.S. states with at least one indexed race | **32 / 50** |
| U.S. states with state-specific official monitoring | **39 / 50** |
| U.S. official-source monitoring entries | **69** |
| All monitoring entries | **115** |
| New Rotax records in both CSV and JSON | **2 / 2** |
| Duplicate event IDs | **0** |
| Sources without exactly one organizer binding | **0** |

Changes committed to `data/races.csv`, `site/events.json`, `data/monitor_sources.json`, `data/organizers.json`, `data/reminder_state.json`, `scripts/build_site.py` and two per-race `.ics` reminder subscription files. The new race IDs are stable under the repository's current SHA-1 event-key rule.

The two `.ics` files intentionally contain no fabricated registration deadline. A verified registration deadline can be added later.

Repository content was re-read and checked after the writes. **Full GitHub CI and live Cloudflare deployment were not independently verified.**

**The comprehensive available-schedules pass across all 50 states is NOT FINISHED.** Continue researching the 11 remaining state-specific monitoring gaps, 2027 club calendars, and exact venues for events still marked TBA.
