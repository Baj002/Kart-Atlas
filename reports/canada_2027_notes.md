# Canada 2027 verification — checkpoint (2026-11-10)

**Scope:** Competitive owner-kart circuit racing (Briggs LO206, Rotax, ROK, shifter, IAME/KA100 and comparable classes). Exclude rental/arrive-and-drive, practice-only, oval/dirt, motocross and unrelated motorsport.

## Generated data (latest independently read: 2026-11-09)

- `site/events.json`: **145 Canadian records** — 141 historical 2026 events and **four announced 2027 weekends**, two in Ontario and two in Quebec. The four 2027 entries remain **Secondary**, not official organizer-page-confirmed. `reports/canada_2027.json` was generated **2026-11-09 15:46 UTC** and audits all **13** provinces/territories.
- **2027 announced dates:** May 28–30 at Académie TAG Karting, Mont-Tremblant QC; June 25–27 at Brechin Motorsports Park ON; July 23–25 at Lombardy Raceway ON; September 3–5 at Karting Trois-Rivières QC. Source: Canadian Karting News report of the organizer's announcement on 2026-10-20: https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/ .
- Official Cup Karts schedule https://www.cupkarts.com/schedule/ still displays **2026** events on November 10. Do not upgrade these four to Official or assign registration URLs/deadlines without an explicit 2027 organizer event or registration page. All four currently lack independently verified 2027 registration links and deadlines.

## Jurisdiction status (verified against the current generated audit)

- **AB, BC, MB, NB, NS, SK:** known eligible competition organizers/sources, but **no 2027 owner-kart race dates verified in the current sources**. This is not a claim that no schedule exists.
- **ON, QC:** two secondary-source 2027 Cup Karts announcements in each province; zero primary-source-confirmed 2027 events in the current generated dataset. Hamilton Karting Complex explicitly says its **2027 HRKC owner-kart schedule is coming soon**: https://hamiltonkartingcomplex.com/ . Quebec's Coupe de Montréal official calendar https://coupedemontreal.com/calendrier-resultats/ still shows 2026.
- **NL, NT, NU, PE, YT:** **no configured verified eligible regional competition source**. These are organizer-discovery gaps, **not evidence of no kart racing**.
- **BC organizer verification improvement (2026-11-10):** Cariboo Kart Racers in Quesnel was upgraded from an unverified directory lead to a reviewed eligible **2026 BC Regional race host**. Both the official West Coast Kart Club 2026 calendar https://www.westcoastkartclub.ca/schedule/ and Vancouver Island Karting Association regional calendar https://vika.ca/bc-regional-races/ identify Quesnel as the June 27–28 race venue (June 26 practice). This establishes 2026 owner-kart competition activity only; a direct Cariboo club calendar and any 2027 dates remain unverified. The existing BC Regional Round 3 is already in `site/events.json`; no duplicate race was added.

## Source reliability and publication gate

- Latest available discovery report `reports/coverage.json` generated **2026-11-09 15:42 UTC**: **105/137** source checks reached, **51** retrieval/parsing errors; **63/85** Canadian source checks reached. Quebec: **4/7** configured regional sources reached. Source reach is not race recall; independent official pages can be readable even if the scanner fails.
- Repository refresh and generated records **do not prove production deployment**. On November 10, both web retrieval of https://kart-atlas.kartatlas.workers.dev/ and its `/events.json` and direct HTTP requests failed; the direct environment also failed DNS resolution for an unrelated major website. Therefore the live application's availability and event-data parity are **not confirmed**.
- **Completion gate remains open:** obtain and index available official 2027 schedules as published; distinguish unpublished versus merely unverified sources; confirm event registration links/deadlines where actually available; improve failed source retrieval and remaining organizer discovery; independently confirm the deployed app and compare its Canadian records with `site/events.json`. Do not fabricate future race dates or declare complete.

Detailed historical research and exclusions: `reports/canada_2027_official_source_review_2026-10-27.md`.
