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

## Follow-up verification — 2026-10-28

The generated 2027 audit now lists **all 13 provinces/territories**, **four Canadian 2027 event records** (two Ontario, two Quebec), and **zero primary-source-confirmed 2027 dates**. All four are labelled Secondary. The four published weekends remain May 28–30, June 25–27, July 23–25 and September 3–5. The official CKNA schedule still shows 2026 events, so the reported 2027 dates must not be silently upgraded to official or assigned 2027 registration deadlines.

**Ontario:** Hamilton Karting Complex explicitly states **“2027 HRKC racing schedule coming soon”** in its club-racing section: https://hamiltonkartingcomplex.com/ . Its dated 2027 non-announcement declaration was reverified on October 28. This applies to the owner-kart HRKC series, **not** the separate rental/arrive-and-drive league.

**Quebec:** Both Coupe de Montréal sources still return HTTP 403 to the repository scanner, despite their public 2026 calendar being visible via external search: https://coupedemontreal.com/calendrier-resultats/ . To improve independent primary-source reach, the monitoring registry now also includes:
- **Ottawa Gatineau Karting Championship / Le Circuit Quyon**: https://www.lecircuitquyon.com/ — the venue explicitly distinguishes competitive karting from rental leagues and says it will reopen in spring 2027, but provides no dated 2027 competition calendar.
- **Académie TAG Karting, Coupe de Montréal host page**: https://www.academietagkarting.com/competitions/coupe-montreal-karting — shows prior Coupe de Montréal rounds; displayed month/day text lacks an explicit 2027 year.
- **SC Performance Karting, Coupe de Montréal host page**: https://scperformance.ca/karting/karting-courses-et-evenements/ — its 2026 page mixes rental SWS series with an owner-kart Coupe de Montréal weekend. Only Coupe de Montréal is eligible; no 2027 dates verified.

These new host sources are monitored with event-name restrictions and explicit rental exclusions. **Adding a monitoring source does not establish that its 2027 calendar has been published or successfully crawled.** The next scheduled discovery run must confirm reach and safe parsing. The organizer registry now links these sources to the correct Quebec leads; OGKC has independent official-track and Quebec federation evidence of competitive karting (https://www.lasq.ca/karting).

**Repository snapshot, 2026-10-28:** 122 Canadian race records across 2026–2027, four 2027 records, 104/131 sources reached, 42 scan errors before the three new sources were added. The 2027 report correctly distinguishes missing-source jurisdictions (NL, NT, NU, PE, YT) from jurisdictions with monitored sources but no verified 2027 dates. No evidence supports claiming the complete 2027 Canadian season is available.

**Deployment remains unconfirmed:** Requests to the public Workers URL and its /events.json were inaccessible from the review environment. Do not mark Canadian coverage complete until the published site and its event payload can be read and compared with repository output. This limitation also prevents confirming that today's registry changes have reached production.

## Follow-up verification — 2026-10-29

**Generated repository snapshot (14:18 UTC):** All 13 Canadian provinces and territories remain represented in the internal audit. `site/events.json` contains **122 Canadian race records**, including **four dated 2027 Cup Karts weekends** (two Ontario, two Quebec). None of the four has an organizer-hosted 2027 event/registration page confirmed; keep their `Secondary` verification and registration deadlines blank. The May 28–30 Nationals now cites the more specific 2026-10-20 Canadian Karting News report rather than the earlier September recap. Official CKNA homepage still shows no upcoming Canadian division events: https://www.cupkarts.com/ .

**Official 2026 calendar checks (2027 dates not established):** CKRC Alberta (https://ckrc.com/event-schedule/), EDKRA Alberta (https://edkra.ca/), WCKC British Columbia (https://www.westcoastkartclub.ca/schedule), VIKA British Columbia (https://vika.ca/race-calendar/), Manitoba Karting Association (https://www.manitobakarting.ca/), South Sask Kart Club (https://www.sskc.ca/schedule), Saskatoon Kart Racers (https://www.nskr.ca/schedule), AMKA Nova Scotia (https://www.amka.ca/), Coupe de Montréal Quebec (https://coupedemontreal.com/calendrier-resultats/), and Ontario's HRKC (https://hamiltonkartingcomplex.com/) still display 2026 competition material or explicitly pending 2027 schedules. The NB CEKS MotorsportReg organizer listing remains the current verified NB competition lead. For NL, NT, NU, PE and YT, **no eligible owner-kart organizer source is yet verified**; this is a discovery gap, not evidence of no racing.

**New British Columbia coverage:** The VIKA official 2026 calendar explicitly lists owner-kart races on **April 4, June 20, September 5 and October 4, 2026** at Vancouver Island Motorsport Circuit; the February 22 and March 15 races were cancelled, and practice-only days are ineligible. Four eligible historical club races were added to `data/races.csv` with direct official source URLs. The official VIKA calendar (https://vika.ca/race-calendar/) and the BC Regional calendar hosted by VIKA (https://vika.ca/bc-regional-races/) were added as monitoring targets and bound to verified organizer identities. The BC Regional series has been upgraded from research lead to reviewed competition organizer on this evidence. Neither page establishes 2027 dates; both are watch-only pending future schedules. These additions are **committed**, not yet confirmed in the generated site.

**Source health (2026-10-29 report, before the two new BC monitors):** **103/133** source origins reached, **43** fetch/parsing errors; Canadian source reach **61/81**. Quebec's primary Coupe de Montréal endpoints remain unreachable to the automated scanner, although the public 2026 calendar can be inspected via external search. Source reach is not a percentage of races covered. The newly added BC sources require a subsequent successful scan before being counted as reached.

**Deployment:** Direct attempts to read the Workers app homepage, `/index.html` and `/events.json` failed from this environment; even a green repository refresh would not prove public deployment. Do not declare the Canada work complete until the deployed site and payload are independently accessible and match the latest generated dataset.

**Outstanding:** Identify active owner-kart organizers in NL, NT, NU, PE and YT where any exist; monitor all known official club calendars for 2027 publication; repair recurrent fetch failures, especially Coupe de Montréal; obtain primary confirmation and registration links for Cup Karts Canada 2027; verify generated events and production deployment. Do not manufacture missing 2027 dates.


## Follow-up verification — 2026-10-30 (09:41 MDT / 15:41 UTC)

**Current generated snapshot:** Latest `site/events.json` (refreshed 2026-10-30 14:14 UTC) contains **126 Canadian race records** and **four Canadian 2027 events**: two Ontario and two Quebec Cup Karts weekends. All four remain **Secondary**, based on the October 20, 2026 Canadian Karting News report of the organizer announcement. No organizer-hosted 2027 event/registration page or deadline was independently verified; do not label these `Official` or invent deadlines. Official CKNA schedule still labels its visible calendar **2026**: https://www.cupkarts.com/schedule/ .

**13-region 2027 evidence review:** AB (CKRC/EDKRA official calendars still show 2026), BC (VIKA/WCKC/BC Regional 2026), MB (MKA 2026), NB (CEKS MotorsportReg 2026), NS (AMKA 2026), ON (HRKC explicitly says 2027 club schedule coming soon; two CKNA 2027 weekends only secondary), QC (Coupe de Montréal official calendar 2026; two CKNA 2027 weekends only secondary), SK (Saskatoon/South Sask 2026). **NL, NT, NU, PE, YT** have no verified active owner-kart competition source configured; this is an **unresolved discovery gap**, not a declaration that no racing exists. For other regions, `no 2027 dates verified in current sources` does **not** establish that every organizer has yet to publish.

**Quebec coverage improvement committed:** Two additional official owner-kart host sources are now watched:
- Karting Trois-Rivières https://kartingtr.com/ explicitly lists 2026 CK3R club races on June 13, September 13 and September 27, distinct from rental karting, supermoto and other disciplines. Added these three historical 2026 races; upgraded existing CK3R organizer to verified competitive scope and linked its new source.
- SRA Karting https://srakarting.com/ecole-de-pilotage/ explicitly lists its 2026 **Ligue SRA** owner-kart race dates on June 21, July 9, August 23 and September 13, with Briggs, Rotax, DD2 and Shifter classes. Added these four historical 2026 races, a verified league organizer, and a dedicated monitor. The October 31 enduro was **not imported** because its exact eligibility/format warrants separate confirmation. Rental/SWS races and practice sessions are excluded.

The seven historical 2026 additions are committed in `data/races.csv`, but are **not yet in the generated `site/events.json`**. The next site build must refresh the public event dataset and diagnostics. JSON source/organizer IDs are unique and organizer source bindings resolve after the change.

**Scanner health:** Latest completed discovery run at 2026-10-30 14:11 UTC reached 105 of 135 attempted sources and reported 43 errors. The two newly added Quebec sources have not yet been scanned. The two Coupe de Montréal endpoints remain flagged unreachable in the generated regional audit despite the official calendar being browser-accessible: https://coupedemontreal.com/calendrier-resultats/ . Continue using independent official host calendars; do not equate HTTP failure with absence of a schedule.

**Deployment:** Live Workers homepage and `/events.json` remained inaccessible from both the web retrieval environment and an independent direct HTTP request (DNS resolution failed in the latter). A GitHub commit or generated dataset is **not** proof of Cloudflare deployment. Completion gate is still **not met**. Verify the new source scan, regenerate data, check 2027 primary event confirmations and registration details, discover missing-region sources where any exist, and compare the publicly deployed events payload to the latest GitHub dataset before declaring Canada substantially complete.

## Follow-up verification — 2026-10-31 (09:40 MDT / 15:40 UTC)

**Generated repository snapshot:** The most recent completed refresh (2026-10-31 13:57 UTC) lists **133 Canadian race records**: **129 dated 2026** and **four dated 2027**. All four 2027 Cup Karts Canada weekends remain **Secondary** (two ON, two QC), with no verified organizer-hosted 2027 event pages, registration URLs or entry deadlines. Canadian Karting News published the organizer's October 20 announcement: https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/ . The primary CKNA schedule https://www.cupkarts.com/schedule/ still displays a **2026** heading and cannot be used as a 2027 event registration source.

**All 13 regions checked:** AB, BC, MB, NB, NS and SK have monitored eligible organizer sources but no additional 2027 dates verified in the reviewed official pages. ON and QC have the four secondary-source 2027 announcements, but their broader official calendars are still 2026 or explicitly pending (HRKC states its 2027 owner-kart schedule is coming soon: https://hamiltonkartingcomplex.com/ ; Coupe de Montréal lists 2026: https://coupedemontreal.com/calendrier-resultats/). NL, NT, NU, PE and YT still lack verified owner-kart competition sources; independent discovery searches returned no eligible official schedules, not evidence that no racing exists. Rental, arrive-and-drive, motocross, practice and unrelated events are excluded.

**New official Ontario history committed:** Point Pelee Karting Club's 2026 owner-kart championship PDF https://www.pointpeleekarting.com/PPKC/assets/pdf/2026/PPKC_2026_Schedule.pdf confirms **12 club rounds** (May 3, 24, 31; June 20, 21; July 11, 18; August 22; September 19, 20, 27; October 4). All 12 have been added to `data/races.csv` with primary-source attribution. Driver development, reserve/rain dates and the three interclub Showdown entries were not imported. The club directory now explicitly records that **2027 race dates have not been verified as of October 31**. These are historical 2026 records, **not** evidence of a 2027 season. The next successful workflow refresh must incorporate them into `site/events.json`; their live availability is not yet established.

**Source-health baseline:** The completed October 31 scanner reached **110/136** configured source origins (Canadian **63/78**) and logged **39** fetch/parsing errors. Quebec reached **4/7** regional origins, so Coupe de Montréal retrieval remains incomplete despite the official page being browser-readable. Source reach is not race coverage.

**Publication gate still unmet:** GitHub updates are committed, but a direct attempt to fetch https://kart-atlas.kartatlas.workers.dev/ and its `/events.json` endpoint failed in the review environment. The current Cloudflare deployment and the newly committed 12 historical Point Pelee records cannot be independently verified. Do not declare completion until the refresh has passed and the live deployed dataset has been compared against the latest repository snapshot.

**Next actions:** Confirm GitHub refresh and generated data after this commit; keep monitoring for organizer-published 2027 schedules and registration deadlines; repair Quebec source retrieval; continue eligible organizer discovery in NL, NT, NU, PE, YT; and verify production deployment. Do not infer a full 2027 schedule from four reported weekends or create speculative dates.
