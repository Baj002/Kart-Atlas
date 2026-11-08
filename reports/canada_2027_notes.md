# Canada 2027 verification — current checkpoint (2026-11-08)

**Scope:** owner-kart competition circuit racing (Briggs LO206, Rotax, ROK, shifter and comparable classes). Rental/arrive-and-drive, practice, oval/dirt, motocross and other disciplines are excluded.

**Current generated data:** `site/events.json` refreshed on 2026-11-08, with 145 Canadian events (141 from 2026; four 2027 Cup Karts Canada weekends). All four 2027 dates remain **Secondary**, not organizer-verified: May 28–30 Mont-Tremblant QC; June 25–27 Brechin ON; July 23–25 Lombardy ON; September 3–5 Trois-Rivières QC. Evidence: https://www.canadiankartingnews.com/2027-schedule-update-cup-karts-canada-reveal-their-dates-and-locations/ . The organizer's https://www.cupkarts.com/schedule/ still displays 2026, so do not mark these Official. No organizer-hosted 2027 registration URLs or registration deadlines verified.

**Jurisdiction audit:** `reports/canada_2027.json` (generated 2026-11-08) covers all 13 provinces/territories. AB, BC, MB, NB, NS and SK have monitored eligible organizer sources but no verified 2027 dates in the current sources; ON and QC contain the four secondary announcements. NL, NT, NU, PE and YT lack configured verified owner-kart competition sources and require organizer discovery. **No verified date does not prove that no schedule is published or that no racing exists.** Hamilton Regional Kart Club explicitly says its 2027 owner-kart schedule is coming soon: https://hamiltonkartingcomplex.com/ .

**Automated refresh:** GitHub Actions runs 42389722316 (Nov 7) and 42487487978 (Nov 8) completed successfully after the Nov 7 organizer-binding fix; `site/events.json` and `reports/canada_2027.json` were regenerated. The Nov 8 scan reached 104 of 137 configured source origins (62 of 85 Canadian), with 50 retrieval/parsing errors. `ckna-canada-news` has now scanned successfully but has not produced primary 2027 event evidence. Source failures are not proof of missing races.

**Deployment gate still open:** Unable to independently retrieve https://kart-atlas.kartatlas.workers.dev/ or its `/events.json` payload from the available web and direct HTTP environments. A successful GitHub refresh does **not** establish live Cloudflare deployment or dataset parity. Do not declare Canadian coverage substantially complete until published schedules have been verified/entered, unpublished or unverified schedules are accurately labelled, and live deployment is confirmed.

Detailed dated verification and eligibility decisions: `reports/canada_2027_official_source_review_2026-10-27.md`.
