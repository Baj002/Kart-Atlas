# Kart Atlas — U.S. 50-state coverage audit, November 12, 2026

**Status: INCOMPLETE.** This is an incremental organizer-source verification pass, not a comprehensive all-50-state available-schedules completion.

## Confirmed published changes

- Added **18 historical 2026 Stockholm Karting Center (SKC) club race days** at **Stockholm Karting Center, Cokato, Minnesota**. This creates the first verified Minnesota race listings in Kart Atlas. Each is a separate one-day owner-kart sprint race; practice and rental sessions were excluded.
- Race days (all 2026): **May 9–10, May 30–31, June 13–14, June 27–28, July 11–12, July 25–26, August 22–23, September 12–13 and September 26–27**. The 18 numbered rounds are supported by the track operator's official monthly calendars:
  - May: https://stockholmkartingcenter.com/events/category/upcoming-events/2026-05/
  - June: https://stockholmkartingcenter.com/events/category/upcoming-events/2026-06/
  - July: https://stockholmkartingcenter.com/events/category/upcoming-events/2026-07/
  - August: https://stockholmkartingcenter.com/events/category/upcoming-events/2026-08/
  - September: https://stockholmkartingcenter.com/events/category/upcoming-events/2026-09/
- The organizer's official website links directly to the event timing/results archive, providing independent corroboration that the series raced: https://stockholmkartingcenter.com/ and https://www.race-monitor.com/Results/Search?searchTerm=stockholm&sectionID=1
- Added the Stockholm official race calendar as a **watch-only source**, bound to the existing Minnesota organizer identity; upgraded the existing organizer record instead of duplicating it.
- Added an official **2027 Formula KFX / Rotax Racing Club California** source as watch-only, bound to the existing organizer. The organizer has published 14 NorCal/SoCal dates and a championship final by **city**, but not specific circuit names for each 2027 round. **No unconfirmed venue was inferred or published.** September 11, August 21 and October 8–10 are marked subject to confirmation by the organizer.
  - Source: https://formulakfx.com/formula-kfx-announces-2027-rotax-racing-club-california-championship-schedule/
  - The separate four-round 2027 Formula KFX Race of Champions announcement is also being tracked for follow-up, but no extra race rows were published without verified circuit identity: https://formulakfx.com/formula-kfx-announces-2027-race-of-champions-invitational-series/

## Verified repository snapshot after this pass

| Metric | Count |
| --- | ---: |
| Total North American indexed races | **411** |
| U.S. indexed races | **258** |
| U.S. races on/after November 12, 2026 | **100** |
| U.S. states with at least one indexed race | **32 / 50** |
| U.S. states with at least one state-specific monitored source | **41 / 50** |
| U.S. monitoring source entries | **65** |
| All monitoring source entries | **111** |
| Minnesota SKC races present in both CSV and JSON | **18 / 18** |
| Duplicate event IDs | **0** |
| Sources without exactly one organizer binding | **0** |

The repository was checked after the updates: every new Minnesota race appears in `data/races.csv` and `site/events.json`, all IDs are unique, the two new watch-only sources are each bound to one organizer, and the site build's curated snapshot was advanced to November 12.

## States without state-specific monitored official sources (11)

**AL, AK, DE, KY, ME, MA, NM, ND, RI, SD, WY**.

These are discovery gaps, **not evidence that the states have no kart racing**. During this pass, several leads were screened and **not** imported because they were outside Kart Atlas's competitive sprint-kart scope:

- **Alabama:** Talladega Gran Prix Raceway advertises owner-kart *open track days*, not a verified competitive race series. https://www.motorsportreg.com/orgs/talladega-gran-prix-raceway
- **Maine:** Mainely Karting advertises a paved *oval* competition facility, excluded by the current scope. https://www.mainelykarting.com/
- **Delaware:** US 13 Kart Club is reported as *clay oval* karting; no eligible paved sprint schedule verified. https://kartdirectory.racing/us/circuit/us-13-kart-club/
- **New Mexico:** ARCOR Raceway's published calendar is for *radio-controlled electric/nitro vehicles*, not full-size go-karts. https://arcorraceway.com/
- **North Dakota:** Red River Kart Club's website reports uncertainty about the 2027 site following a land sale; no qualifying 2027 sprint-kart venue/date was verified. https://www.redriverkartclub.com/

The remaining states need additional official-organizer discovery or verified 2027 competition calendars. No dates were projected from prior seasons.

## Publication and remaining work

Committed to `data/races.csv`, `site/events.json`, `data/monitor_sources.json`, `data/organizers.json` and `scripts/build_site.py`. All 18 new races are historical 2026 records; **this pass did not add any upcoming races**. The 2027 Formula KFX schedule is monitored but not published as individual race rows pending exact venue confirmation.

Full CI/test execution and live Cloudflare deployment were not independently verified.

**The comprehensive available-schedules pass across all 50 U.S. states is NOT FINISHED.** Continue researching the 11 state-specific source gaps, monitoring official 2027 club schedules, and confirming exact circuit venues before import.
