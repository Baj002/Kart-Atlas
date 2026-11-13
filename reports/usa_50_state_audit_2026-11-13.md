# Kart Atlas — U.S. 50-state coverage audit, November 13, 2026

**Status: INCOMPLETE.** This is an incremental verified-organizer pass, not an exhaustive audit of all published eligible schedules in all 50 states.

## Substantive verified changes

1. **19 historical 2026 Road America Karting Club sprint race days** added in Wisconsin at **Briggs & Stratton Motorplex, Plymouth, WI**. Eight weekend championship rounds and eleven weeknight rounds are explicitly listed on Road America's official 2026 results page:
   - Weekend: May 9, May 23, June 27, July 11, August 22, September 5, September 26, October 10.
   - Weeknight: June 2, June 16, June 23, June 30, July 7, July 21, July 28, August 4, August 11, August 25 (Round 12), August 27 (Round 11 makeup).
   - Official track/organizer race-results index: https://www.roadamerica.com/karting-club
   - Organizer's RaceSelect registration archive corroborates the event series and venue: https://raceselect.com/road-america-karts/2026
   - **Excluded** the August 29 weekend rainout and the weeknight Round 6 because organizer results and registration dates conflict (July 14 versus July 23). Excluded rental-only activities, non-points races, and membership registrations.
   - The existing Road America Karting Club organizer record was upgraded rather than duplicated; its official results URL was added as a watch-only monitoring source for future 2027 publications.

2. **Two existing 2027 Florida Winter Tour rounds corrected** following the **November 12, 2026 ROK Cup USA announcement** confirming **Orlando Kart Center, Orlando, Florida**:
   - Round 2: February 26–28, 2027.
   - Round 3: March 12–14, 2027.
   - Official confirmation: https://rokcupusa.com/rok-cup-usa-confirms-orlando-kart-center-for-rounds-2-and-3-of-the-2027-florida-winter-tour/
   - The older general calendar https://rokcupusa.com/calendar/ still showed TBA at review time; the more recent specific announcement is controlling evidence. Dates were unchanged.
   - Removed two redundant curated CSV rows for these same rounds. The canonical race IDs **c221825c977a** and **f6380f404a97** and their former alias IDs were preserved through a stable-ID build mapping, protecting saved race references.
   - Added the official confirmation page as a separate watch-only source, bound to the existing ROK Cup USA organizer.

3. **One incorrect conditional event removed:** the automated **April 18, 2027 PKRA rain make-up date** is a contingency, not a confirmed championship race. The official PKRA schedule labels it a rain date: https://pkra.com/racing-schedule/. Added an explicit scope exclusion so it does not return during a rebuild.

## Post-write repository integrity

| Metric | Verified value |
| --- | ---: |
| Total indexed North American races | **429** |
| U.S. race records | **276** |
| U.S. race records on or after November 13, 2026 | **98** |
| States with at least one indexed U.S. race | **32 / 50** |
| States with at least one **state-specific** monitored U.S. source | **39 / 50** |
| U.S. monitoring entries (includes multistate sources) | **67** |
| All monitoring entries | **113** |
| New Road America races present in both CSV and JSON | **19 / 19** |
| Duplicate event IDs in published JSON | **0** |
| Monitoring entries without exactly one organizer binding | **0** |
| Incorrect conditional PKRA rain event still published | **0** |

The state-specific count intentionally excludes monitoring entries with regions labeled `Multi` or `Various`; it must not be confused with the total number of organizer sources.

## Remaining 11 state-specific monitoring gaps

**AL, AK, DE, KY, ME, MA, NM, ND, RI, SD, WY.**

These are **research/source gaps**, not claims that no karting exists. The following candidates were screened but were **not** added as qualifying competitive sprint-kart sources:

- **Alabama:** Talladega Gran Prix Raceway advertises open kart track days rather than a verified championship schedule: https://www.motorsportreg.com/orgs/talladega-gran-prix-raceway
- **Kentucky:** NCM Kartplex primarily advertises rental kart sessions, not a verified owner-kart sprint championship: https://www.motorsportspark.org/event-calendar/
- **Maine:** Mainely Karting operates an asphalt **oval**, outside Kart Atlas's sprint circuit scope: https://www.mainelykarting.com/
- **New Mexico:** ARCOR Raceway is for radio-controlled cars, not full-size karts: https://arcorraceway.com/
- **North Dakota:** Red River Kart Club published 2026 events but has unresolved 2027 venue uncertainty after a land sale; sprint circuit eligibility also requires verification: https://www.redriverkartclub.com/
- **South Dakota:** University Plains Speedway is a dirt/clay oval, excluded: https://visitbrookingssd.com/event/sd-state-championship-at-university-plains-speedway/

No unverified race dates or circuit names were imported. No state was marked covered merely because a directory lead or rental track exists.

## Publication and next work

Committed to `data/races.csv`, `site/events.json`, `data/monitor_sources.json`, `data/organizers.json`, `data/racing_scope.json`, and `scripts/build_site.py`. The two FWT changes are **venue corrections, not newly scheduled races**. All 19 new events are **historical 2026 races**.

Post-write content and binding checks passed. **Full GitHub CI execution and the live Cloudflare deployment were not independently verified.**

**The comprehensive available-schedules pass across all 50 U.S. states is NOT FINISHED.** Continue checking the 11 state-specific source gaps, 2027 official club calendars, and newly announced exact race venues. Do not infer future dates from prior seasons.
