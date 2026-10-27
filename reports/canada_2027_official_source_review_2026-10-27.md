# Canada 2027 kart calendar — official-source review (2026-10-27)

**Scope:** owner-kart competitive circuit racing (LO206, Rotax, ROK, IAME, shifter and equivalent); exclude rentals, practice, oval/dirt, motocross and other disciplines. This is an **internal evidence log**, not a public schedule.

## Confirmed dated 2027 announcements

Four 2027 Canadian Cup Karts weekends are already represented in `site/events.json`, all marked **Secondary** pending direct organizer event pages. Canadian Karting News reported the series organizer's announcement on **2026-10-20**:
https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/

| Dates (2027) | Event | Province | Venue | Source grade |
| --- | --- | --- | --- | --- |
| May 28–30 | Canadian Four-Cycle Nationals | QC | Académie TAG Karting, Mont-Tremblant | Organizer announcement reported by CKN; primary event page not verified |
| June 25–27 | Cup Karts Canada Division R1 | ON | Brechin Motorsport Park | Same |
| July 23–25 | Cup Karts Canada Division R2 | ON | Lombardy Raceway | Same |
| Sept 3–5 | Cup Karts Canada Division finale | QC | Karting Trois-Rivières | Same |

The organizer's public schedule https://www.cupkarts.com/schedule/ still surfaced 2026 event details at review time. **Do not promote these four to Official** without a direct organizer page or primary confirmation. No verified 2027 registration URLs or registration deadlines were found for these four.

## Official pages reviewed; 2027 status

| Jurisdiction | Official sources reviewed | Evidence status on 2026-10-27 |
| --- | --- | --- |
| AB | https://ckrc.com/event-schedule/ ; https://edkra.ca/pages/registration | CKRC page shows 2026 championship dates; EDKRA directs to MotorsportReg. No 2027 competition dates verified from these pages. CKRC's separate Try-A-Kart page explicitly says its **Try-A-Kart** 2027 dates are not posted; that is **not** evidence about the club racing season. |
| BC | https://www.westcoastkartclub.ca/schedule ; https://vika.ca/bc-regional-races/ | WCKC/BC Regional published 2026; no 2027 dates verified. |
| MB | https://www.manitobakarting.ca/ ; https://www.motorsportreg.com/orgs/manitoba-karting-association | 2026 information; no 2027 competition dates verified. |
| NB | https://www.motorsportreg.com/orgs/canada-east-kartsport-champlain-mp | CEKS public organizer listing shows 2026 entries; no 2027 race dates verified. |
| NL | No active owner-kart competition organizer source verified in current registry | **Source discovery gap**, not proof that no racing exists. |
| NS | https://www.amka.ca/race-schedule | Explicit 2026 championship race calendar; no 2027 dates verified. |
| NT | No active owner-kart competition organizer source verified in current registry | **Source discovery gap**, not proof that no racing exists. |
| NU | No active owner-kart competition organizer source verified in current registry | **Source discovery gap**, not proof that no racing exists. |
| ON | https://hamiltonkartingcomplex.com/events/ ; https://rmcontario.com/ ; https://bscontario.com/schedule/ | HRKC/RMC/BSC public pages currently show 2026 events. BSC Ontario is a verified owner-kart Briggs championship newly added to monitoring. No independent 2027 dates verified from these pages; two Cup Karts weekends reported by CKN as above. |
| PE | No active owner-kart competition organizer source verified in current registry | **Source discovery gap**, not proof that no racing exists. |
| QC | https://coupedemontreal.com/calendrier-resultats/ ; https://maxchallenge.ca/ | Coupe de Montréal and Rotax sources show 2026; no independent 2027 race dates verified; two Cup Karts weekends reported by CKN. Quebec monitoring also has unresolved source-fetch failures. |
| SK | https://www.sskc.ca/schedule ; https://www.nskr.ca/schedule | Both clubs show 2026 schedules; no 2027 race dates verified. |
| YT | No active owner-kart competition organizer source verified in current registry | **Source discovery gap**, not proof that no racing exists. |

**Interpretation:** “No 2027 dates verified” means only that this check did not establish a published, eligible 2027 date. It must **not** be rewritten as “the organizer has not published a schedule” unless an official statement establishes that fact. Provincial source coverage is not a census of clubs.

## Repository and publication checks

- `reports/canada_2027.json` audits all 13 jurisdictions, including source health and missing registration data.
- `reports/coverage.json` on 2026-10-27 reports **98/130** source origins reached, **44** fetch/parsing errors and **0/2** Quebec regional source origins reached. These are operational gaps, not race-coverage percentages.
- `site/events.json` on 2026-10-27 contained **119 Canadian records**, **four dated 2027 events**, and one future 2026 Canadian event. The four 2027 entries lack verified registration links and deadlines.
- Three official 2026 BSC Ontario championship weekends have been backfilled in `data/races.csv` (historical reference); their appearance in the generated site depends on the next successful refresh.
- **Live deployment is not confirmed:** direct requests to the Workers site were unavailable from this review environment. Repository updates and a green build, if obtained, do not substitute for checking the public `events.json` and map.
- Remaining blockers: verify primary Cup Karts 2027 event pages; monitor official provincial schedules as released; improve Quebec source reach and Ontario organizer coverage; identify verified organizers/sources in NL, NT, NU, PE, YT; verify generated dataset and live deployment after refresh.

This document is a dated research snapshot; the daily generated `reports/canada_2027.json` and official source pages remain authoritative for newer changes.
