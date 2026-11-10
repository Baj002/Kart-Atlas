# Kart Atlas — U.S. 50-state coverage audit, November 10, 2026

**Status: INCOMPLETE.** This is a verified incremental organizer-schedule pass, not a comprehensive available-schedules pass across all 50 states.

## Verified publication results

- Indexed events (all North America): **379**.
- U.S. events: **226** across **30** states.
- U.S. upcoming events from November 10, 2026: **95**.
- U.S. state-tagged monitored official-source entries: **54** across **35** states (national/multi-state registry entries excluded from state count; some state-tagged records point to a particular race on a multi-state organizer schedule).
- New U.S. curated race records this pass: **47**, including **5 future 2027 Texas Sprint Racing Series rounds** and **42 verified historical 2026 events**.
- New state race coverage: **Mississippi, New Jersey, Washington**. The Louisiana 2027 TSRS event also has a newly monitored official source.
- New official monitoring entries: **6** (all watch-only; no speculative automatic publication).
- Santa Maria Kart Association Round 8 corrected from the old secondary October 25 listing to the official **October 18, 2026** date. The stable saved-event ID is preserved through the reviewed override.

## New 2027 races with confirmed venues

| Date | Series | Venue | State |
| --- | --- | --- | --- |
| Feb 26–28, 2027 | TSRS Round 1 | Speedsportz Racing Park, New Caney | TX |
| Apr 2–4, 2027 | TSRS Round 2 | North Texas Karters, Denton | TX |
| Apr 30–May 2, 2027 | TSRS Round 3 | Amarillo Motorsports Park, Panhandle | TX |
| Jul 9–11, 2027 | TSRS Round 4 | NOLA Motorsports Park, Avondale | LA |
| Aug 27–29, 2027 | TSRS Round 5 | Oklahoma Motorsports Complex, Norman | OK |

**Official organizer:** https://www.texassprintseries.com/
Individual round pages: https://www.texassprintseries.com/round-4/ and https://www.texassprintseries.com/round-5/

## Verified historical additions by source

- **PSGKA / Washington:** Eight 2026 owner-kart club championship races plus the NWKA Super Cup at Mountain Highway Raceway; no rental, vintage or time-attack listings. Source: https://psgka.com/psgka-racing/
- **CKNA / multi-state:** Twelve 2026 owner-kart events across MS, NJ, FL, NC, TN, WI, NY, OH, IL and IN. NJMP independently confirms its August 28–30 event; CKNA registration also corroborates the weekend. Sources: https://www.cupkarts.com/schedule/ and https://njmp.com/event/cup-karts-liberator/
- **New Castle / Indiana:** Fourteen 2026 Kart Racers Association club rounds from the track's published owner-kart schedule. Source: https://newcastlemotorsportspark.com/schedule
- **Santa Maria / California:** Seven 2026 owner-kart club rounds, plus the corrected previously indexed eighth round. Source: https://www.smka.org/the-track/race-day-info/

## Data integrity and publication

- Files updated: `data/races.csv`, `site/events.json`, `data/monitor_sources.json`, `data/organizers.json`, `data/racing_scope.json`, and `scripts/build_site.py` (curated snapshot date).
- Newly added race IDs were generated using the same SHA-1 start-date/name/venue key as the repository's `scripts/build_site.py`.
- Existing event IDs were checked; **zero duplicate event IDs** after this pass. The 47 new CSV records were cross-checked against the published JSON by event name, date and venue, with no missing mappings. Four official organizer records were verified or rebound to monitored sources. An additional 19 pre-existing unbound monitoring entries were repaired by binding them to 13 existing and six newly registered organizers; all 105 monitoring IDs now have exactly one organizer binding, with no alias collisions.
- Source-specific dates and venues were verified against organizer or track schedules; no 2027 date was inferred from a 2026 recurrence.
- The two-day CKNA Biloxi event is represented as Feb 20–22 per the official CKNA calendar; RaceSelect's wider administrative date window extends through Feb 24. Event/race-day schedule is the authoritative source.
- No CI test execution or Cloudflare deployment status was independently confirmed. The repository may rebuild `site/events.json` and reminder calendars on its next workflow run.

## Remaining source-monitoring gaps

**15 states without a state-specific monitored official kart race source:** AL, AK, DE, HI, KY, ME, MA, MN, MT, NM, ND, RI, SD, VA, WY.

Do not interpret the lack of monitored sources as no kart racing. Many candidate tracks in these regions are rental-only, dirt/oval, vintage, or long-circuit road-racing operations; only verified owner-kart sprint/circuit racing is eligible.

The comprehensive available-schedules pass across all 50 U.S. states is **NOT FINISHED**. Next work: verify eligible official organizers in the 15 remaining states, monitor new 2027 club calendars as they are published, reconcile source date conflicts, and run the repository build and tests.
