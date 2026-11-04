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

## Follow-up verification — 2026-11-01 (09:44 MST / 15:44 UTC)

**Fresh generated dataset:** The November 1 GitHub refresh (events updated `2026-11-01`, discovery scan `2026-11-01T13:56:11Z`) contains **145 Canadian records: 141 historical 2026 and four 2027**. The October 31 Point Pelee backfill has therefore reached the generated repository data. The four 2027 CKNA weekends remain **Secondary**: May 28–30 (Mont-Tremblant, QC), June 25–27 (Brechin, ON), July 23–25 (Lombardy, ON), and September 3–5 (Trois-Rivières, QC). None has a verified organizer-hosted 2027 event page, event registration URL or deadline. Dates were reported from the October 20 CKNA organizer announcement by Canadian Karting News: https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/ . The primary CKNA site still explicitly labels its calendar **2026**: https://www.cupkarts.com/schedule/ . Do not substitute its 2026 registration links for 2027.

**Region-by-region 2027 check (13 of 13 jurisdictions):**

| Region | Indexed Canadian races (all years) | 2027 verified/announced | Latest official source status |
| --- | ---: | --- | --- |
| AB | 38 | 0 | CKRC and EDKRA official race pages still show 2026; no 2027 owner-kart race dates verified. https://ckrc.com/event-schedule/ ; https://edkra.ca/pages/schedule-events |
| BC | 16 | 0 | WCKC, VIKA and BC Regional monitored; official calendars still refer to 2026. https://www.westcoastkartclub.ca/schedule ; https://vika.ca/race-calendar/ |
| MB | 11 | 0 | MKA 2026 information; no 2027 owner-kart dates verified. https://www.manitobakarting.ca/ |
| NB | 1 | 0 | CEKS MotorsportReg organizer listing currently shows 2026 entries. AMKA independently confirms 2026 interclub racing in Dieppe; no 2027 NB owner-kart schedule verified. https://www.motorsportreg.com/orgs/canada-east-kartsport-champlain-mp ; https://www.amka.ca/race-schedule |
| NL | 0 | 0 | No eligible owner-kart organizer verified; public rental/amusement tracks are not evidence of a championship. **Source discovery gap.** |
| NS | 9 | 0 | AMKA official championship calendar explicitly shows 2026, with 10 rounds across NS and NB. https://www.amka.ca/race-schedule |
| NT | 0 | 0 | No eligible owner-kart organizer verified. NWT Motorsports Club explicitly describes car-only autoslalom/off-road/ice events, not kart racing. **Source discovery gap.** https://nwtmc-yk.wixsite.com/nwtmc |
| NU | 0 | 0 | No eligible owner-kart organizer verified. **Source discovery gap.** |
| ON | 30 | 2 announced, 0 primary-confirmed | Two CKNA 2027 weekends are Secondary. HRKC explicitly says its 2027 owner-kart schedule is coming soon (rechecked November 1); other club calendars reviewed still show 2026. https://hamiltonkartingcomplex.com/ ; https://bscontario.com/schedule/ |
| PE | 0 | 0 | No eligible owner-kart organizer verified; publicly indexed Burlington and Cavendish venues advertise rental/amusement karting, not a verified owner-kart championship. **Source discovery gap.** https://www.tourismpei.com/attractions/burlington-go-karts-and-amusement-park |
| QC | 17 | 2 announced, 0 primary-confirmed | Two CKNA 2027 weekends are Secondary. Coupe de Montréal still publishes its 2026 calendar. https://coupedemontreal.com/calendrier-resultats/ |
| SK | 23 | 0 | South Sask and Saskatoon monitored official schedules show 2026. https://www.sskc.ca/schedule ; https://www.nskr.ca/schedule |
| YT | 0 | 0 | No eligible owner-kart organizer verified. **Source discovery gap.** |

**Source-health diagnostics:** The latest completed scan reached **104/136** configured source origins (Canadian **62/84**) and logged **47** fetch/parsing errors, compared with 110/136 and 39 errors on October 31. These counts are operational reach, **not** race-coverage percentages. Coupe de Montréal official endpoints still return HTTP 403 to the scanner; its calendar remains independently readable and currently says 2026. EDKRA's schedule endpoint returned 404 to the scanner, but the same official URL was independently readable on November 1 and still showed 2026, indicating a retrieval-path problem rather than a missing organizer. Newer QC host monitors mostly reached, while SRA remains unreachable. Preserve already verified events on fetch failures.

**Repository improvement:** Refreshed Hamilton Regional Kart Club's evidence-backed 2027 `not_announced` season declaration to November 1 in `data/organizers.json`. This is the only explicit owner-kart 2027 schedule-coming-soon statement established here; absence of verified dates elsewhere must not be misrepresented as an official non-announcement.

**Publication and completion gate:** The generated repository events now include the October 31 historical backfill, but independent attempts to fetch https://kart-atlas.kartatlas.workers.dev/ and its `/events.json` endpoint failed from both the web tool and direct HTTP/DNS in the execution environment. **Live Cloudflare deployment is not confirmed** and cannot be inferred from a refreshed GitHub dataset. Keep Canadian coverage open pending (1) primary organizer 2027 dates as published, (2) verified registration information, (3) improved Quebec/other source reach and discovery in NL/NT/NU/PE/YT, and (4) a successful production payload comparison. No speculative dates were created.


## Follow-up verification — 2026-11-02

**Fresh repository state:** `site/events.json` is dated **2026-11-02** and contains **145 Canadian races** (141 from 2026; four from 2027), unchanged from November 1. All four 2027 CKNA weekends remain **Secondary**, with no organizer-hosted 2027 registration URL or registration deadline. The dates are May 28–30 (QC), June 25–27 (ON), July 23–25 (ON) and September 3–5 (QC). The organizer's official schedule still says **CKNA 2026 Schedule**, and its visible registration buttons are associated with 2026 entries; do **not** reuse them for 2027: https://www.cupkarts.com/schedule/ . The October 20, 2026 secondary report of the organizer announcement remains the basis for the four dates: https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/ .

**Official-source spot checks (2027 status):**
- **AB:** CKRC's official calendar still displays its 2026 championship and moved Race 1 (May 24); EDKRA's official race page still displays 2026 club and DD2 calendars, including rescheduled club rounds 1/2/4. The 2026 EDKRA dates were cross-checked against existing Kart Atlas entries; the rescheduled dates match. Neither page established a 2027 competition date. https://ckrc.com/event-schedule/ ; https://edkra.ca/pages/schedule-events
- **BC:** West Coast Kart Club's official schedule still explicitly displays 2026 WCKC and BC Regional dates. https://www.westcoastkartclub.ca/schedule
- **MB:** MKA remains configured and its 2026 records remain indexed; no 2027 owner-kart event was verified in this review. https://www.manitobakarting.ca/
- **NB/NS:** AMKA's official page remains headed **2026 AMKA Championship Race Schedule**, with its NB interclub round and NS races; no 2027 owner-kart event verified. https://www.amka.ca/race-schedule
- **ON:** Hamilton Karting Complex explicitly says **2027 HRKC racing schedule coming soon**, separately from its rental arrive-and-drive programme. Other monitored Ontario organizers remain in discovery; two 2027 CKNA dates are still secondary-only. https://hamiltonkartingcomplex.com/
- **QC:** Coupe de Montréal's official results/calendar page remains headed **2026**, and the two 2027 CKNA dates remain secondary-only. A newly surfaced **LCKQ Hivernale 2026/2027** programme is expressly a *supplied rental-kart* league and must **not** enter Kart Atlas owner-kart competition: https://coupedemontreal.com/calendrier-resultats/ ; https://www.kcr-karting.com/lckq-hivernale
- **SK:** Saskatoon Kart Racers' official schedule remains **2026**. Its September 27 make-up race and other club rounds match the existing indexed entries. https://www.nskr.ca/schedule
- **NL, NT, NU, PE, YT:** No verified eligible owner-kart organizer/source found in targeted November 2 searches. PEI's Burlington Go-Karts is a rental/amusement attraction, not a qualifying owner-kart competition source: https://www.tourismpei.com/attractions/burlington-go-karts-and-amusement-park . Searches for the other four jurisdictions did not establish eligible organizers. These remain **discovery gaps**, not statements that kart racing is absent.

**Fresh scanner diagnostics:** `site/coverage.json` reports **2026-11-02T14:28:23Z**, **111/136** source origins reached, including **64/78** Canadian origins, and **41** retrieval/parsing errors. The Canadian regional breakdown is AB 2/4, BC 6/6, MB 3/3, NB 1/1, NS 1/1, ON 14/14, QC 4/7, SK 2/2, with no configured regional sources in NL/NT/NU/PE/YT. Source-origin reach is not a race coverage percentage. CKRC and Coupe de Montréal continue returning 403 to the automated fetcher, and EDKRA's schedule URL returns 404 to that fetcher despite independently readable official pages. Do not delete previously verified events based on fetch errors.

**Data integrity spot check:** 13 Canadian jurisdictions appear in the generated audit; Canadian event totals by region are AB 38, BC 16, MB 11, NB 1, NL 0, NT 0, NS 9, NU 0, ON 30, PE 0, QC 17, SK 23, YT 0. These sum to 145. Four 2027 entries have no verified registration URLs/deadlines, so registration deadline reminders cannot yet be trusted for those races. Excluded rental racing, motocross, and unrelated motorsport 2027 dates found in broad search.

**Deployment:** Attempts to retrieve both https://kart-atlas.kartatlas.workers.dev/ and `/events.json` through independent web retrieval failed. Direct HTTP checks from this environment failed at DNS resolution, so the deployed app and production event payload remain **unverified**, not proven down. GitHub dataset freshness alone does not establish Cloudflare deployment. Continue monitoring and do not declare completion until the live site is reachable and its event data agrees with the repository.

## Follow-up verification — 2026-11-03

**Generated dataset:** The November 3 refresh (`site/events.json` updated `2026-11-03`) still has **145 Canadian records**, 141 historical 2026 races and four announced 2027 Cup Karts Canada weekends. The four are **Secondary**: May 28–30 at TAG Karting Academy in Mont-Tremblant (QC); June 25–27 at Brechin Motorsports Park (ON); July 23–25 at Lombardy Raceway (ON); September 3–5 at Karting Trois-Rivières (QC). The October 20, 2026 Canadian Karting News article reports the announcement: https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/ . The official CKNA schedule is still explicitly headed **CKNA 2026 Schedule**: https://www.cupkarts.com/schedule/ . The official CKNA news listing currently shows its latest dated article as October 14, 2026, not a 2027 Canada event detail/registration notice: https://www.cupkarts.com/news/ . No organizer-hosted 2027 event registration page, deadline or class-specific 2027 bulletin was verified; do not reuse 2026 registration links.

**Monitoring improvement:** Added `ckna-canada-news` to `data/monitor_sources.json` as a separate, **watch-only** official CKNA news source, with `region=Multi`, `auto_import=false`, and a note to review Canadian event announcements manually. This complements the existing official CKNA schedule monitor. It is a monitoring source, **not** primary verification of the four secondary-announced dates, and its first scan has not yet completed. Source IDs were checked for duplicates before commit.

**All 13 jurisdictions — official-source evidence and publication status:**
- **AB:** CKRC and EDKRA monitored; neither reviewed official 2026 schedule establishes a 2027 race date. https://ckrc.com/event-schedule/ ; https://edkra.ca/pages/schedule-events
- **BC:** WCKC's official site still explicitly lists its 2026 club championship and BC Regional dates; VIKA and Kartplex remain monitored. No 2027 owner-kart date verified. https://www.westcoastkartclub.ca/schedule
- **MB:** Manitoba Karting Association's official site links its existing event calendar and 2026 season; no verified 2027 race date. https://www.manitobakarting.ca/
- **NB:** CEKS is monitored; AMKA's 2026 official calendar includes its August 9 New Brunswick interclub round. No 2027 owner-kart date verified. https://www.amka.ca/race-schedule
- **NL:** No configured eligible competition organizer/source or verified 2027 race date. Discovery unresolved; absence of a source does not prove absence of racing.
- **NS:** AMKA's official schedule remains titled 2026 and includes nine Nova Scotia championship rounds. No 2027 owner-kart date verified. https://www.amka.ca/race-schedule
- **NT:** No configured eligible competition organizer/source or verified 2027 race date; discovery unresolved.
- **NU:** No configured eligible competition organizer/source or verified 2027 race date; discovery unresolved.
- **ON:** Two CKNA dates reported by secondary source. Hamilton Karting Complex explicitly says **2027 HRKC racing schedule coming soon** for owner-kart racing; its separate rental-kart program must not be imported. BSC Ontario's official calendar is headed 2026. https://hamiltonkartingcomplex.com/ ; https://bscontario.com/schedule/
- **PE:** No configured eligible competition organizer/source or verified 2027 race date; rental/amusement karting is not qualifying evidence.
- **QC:** Two CKNA dates reported by secondary source. Coupe de Montréal's official calendar is still headed 2026, with seven rounds; no verified 2027 organizer event page. The LCKQ winter 2026–27 league supplies rental karts and is **excluded**. https://coupedemontreal.com/calendrier-resultats/ ; https://www.kcr-karting.com/lckq-hivernale
- **SK:** Saskatoon Kart Racers' official calendar is headed 2026, including its September 27 makeup round; South Sask remains monitored. No 2027 owner-kart date verified. https://www.nskr.ca/schedule
- **YT:** No configured eligible competition organizer/source or verified 2027 race date; discovery unresolved.

**November 3 scanner health (before new CKNA news source is scanned):** `reports/coverage.json` generated `2026-11-03T14:25:41Z` reports **106/136** total source origins reached, **64/84** Canadian origins reached and **45** retrieval/parsing errors. Regional Canadian origin reach: AB 2/4; BC 6/6; MB 3/3; NB 1/1; NS 1/1; ON 14/14; QC 4/7; SK 2/2; NL/NT/NU/PE/YT 0 configured. The persistent Coupe de Montréal 403s and other fetch failures are **source health failures**, not proof of no races. Origin reach is not event-discovery completeness.

**Data integrity and scope:** All 13 Canadian jurisdictions are represented in the generated audit. Canadian event counts: AB 38, BC 16, MB 11, NB 1, NL 0, NS 9, NT 0, NU 0, ON 30, PE 0, QC 17, SK 23, YT 0 (total 145). No new verified 2027 dates or registration deadlines were established. Do not infer a full 2027 calendar from four announced weekends, do not import rental racing or other motorsports, and do not assume a 2027 schedule is unpublished solely because this scan found none.

**Deployment gate:** Independent requests to the Cloudflare Workers homepage and `/events.json` remain inaccessible from the available web retrieval environment. Repository regeneration and the new source-monitor commit **do not** establish that the deployed PWA is current. Production confirmation still requires a successful live page and event-payload comparison. **Canadian coverage is not substantially complete**; keep the task active.


## Follow-up verification — 2026-11-04

**Repository and generated calendar:** `site/events.json` is still dated 2026-11-03; `site/monitor_status.json` reports the last scan at 2026-11-03T14:25:41Z (106/136 source checks, 45 errors). The last verified Canadian breakdown remains 145 records: 141 historical 2026 entries and four secondary-source announced 2027 Cup Karts Canada weekends. No new organizer-confirmed 2027 Canadian owner-kart event or registration deadline was established on November 4. Do not promote secondary dates to Official without an organizer-hosted announcement.

**Fresh independent source checks (2026-11-04):** Canadian Karting News's October 20 report still supports the four 2027 Cup Karts announcements (https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/). Coupe de Montréal's official calendar remains expressly labeled 2026 (https://coupedemontreal.com/calendrier-resultats/). Mosport Karting Centre advertises its MIKA owner-kart program but links a 2026 race schedule, not verified 2027 dates (https://www.mosportkartingcentre.com/). RMC Ontario's official 2026 schedule remains the relevant dated series document (https://rmcontario.com/2026-rmc-ontario-and-rmc-quebec-dates-and-locations/). These checks do not establish that all 2027 schedules are unpublished.

**Eligibility safeguards:** Hamilton Karting Complex's November 7, 2026 Race of Champions is explicitly an arrive-and-drive Canadian Mini Indy event and must not be imported as owner-kart racing (https://hamiltonkartingcomplex.com/event/race-of-champions-arrive-drive/). KCR's winter 2026–27 LCKQ series explicitly supplies rental karts and must remain excluded (https://www.kcr-karting.com/lckq-hivernale). An independently discovered 2027 Triple Crown calendar is motocross, not karting (https://www.triplecrownseries.ca/).

**Jurisdictional completeness:** AB, BC, MB, NB, NS, ON, QC and SK retain competition-source leads; NL, NT, NU, PE and YT remain unresolved organizer-discovery gaps, not confirmed absence of racing. No newly verified owner-kart 2027 dates were identified in the other jurisdictions during this check. The November 3 jurisdiction-level findings remain the latest documented full sweep.

**Production deployment:** Independent attempts to open both https://kart-atlas.kartatlas.workers.dev/ and https://kart-atlas.kartatlas.workers.dev/events.json failed in the web retrieval environment on November 4. This is an inability to verify deployment, not proof of downtime. No production/repository parity claim can be made. **Completion gate remains unmet**; continue monitoring and verify live deployment before notifying the user of completion.
