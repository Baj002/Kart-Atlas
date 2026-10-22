# Kart Atlas website notifications

Implementation is prepared and tested. Live delivery is **not enabled** until the owner's Cloudflare account, public site origin, D1 database and VAPID secrets are connected. The static website and calendar exports continue to work without a backend; the notification control explains its unavailable state.

## What a racer does

Save races → Manage reminders → choose the lead time → Enable website notifications → allow the browser permission. On iPhone/iPad (iOS 16.4+) first add Kart Atlas to the Home Screen and open it there. Android supports compatible browsers. No app-store enrollment, email or Kart Atlas login is needed. Browser support is detected, not assumed.

Phone notifications are independently opt-in from the existing in-app reminders. The per-race include toggles and lead time apply to both. Unsave/mute changes are sent to the backend when connected. Turning notifications off unsubscribes the browser and requests server deletion; offline deletion is retried on reopening. Permissions, Focus, connectivity and power settings can delay or suppress alerts. Delivery is not guaranteed.

## One-time activation (owner's Cloudflare account)

These are operator instructions. Do not put credentials in chat, git, public variables or screenshots. The setup helper only creates local ignored files and never uploads secrets. Confirm the current website URL **before** moving hosting: saved races and installed PWAs belong to that origin. A different domain is a separate installation.

1. Authorize the Cloudflare CLI with `npx wrangler login`. Create a D1 database with `npx wrangler d1 create kart-atlas-push`. Record its UUID.
2. Run `npm run push:configure -- origin=https://YOUR-PUBLIC-SITE contact=YOUR-EMAIL database=THE-D1-UUID`. Keep the generated `push/.keys/vapid.json` private and backed up. Do not regenerate/rotate VAPID keys on routine deploys; browsers bind subscriptions to them.
3. Apply the database schema: `npx wrangler d1 migrations apply DB --remote --config push/wrangler.json`.
4. Deploy: `npx wrangler deploy --config push/wrangler.json`. This Worker can serve the existing site assets as well as the API. If preserving an existing Cloudflare Pages custom domain, route only `/api/push/*` to this Worker and update the Pages assets separately. A `pages.dev` address cannot simply be attached as a Worker route: review the hosting arrangement first. Set `SITE_ORIGIN` to the actual public frontend origin. The Worker must receive the frontend's `/api/push/*` requests at the same origin; the browser does not use cross-origin credentials or API overrides.
5. Upload secrets directly: `npx wrangler secret bulk push/.keys/vapid.json --config push/wrangler.json`. This updates the Worker without exposing key values in git. Verify `/api/push/config` returns `enabled: true` at the frontend URL. It exposes the public VAPID key only.

The cron is configured to run every five minutes. New triggers may take time to propagate. The deployment needs Workers/D1 and the rate-limit binding; account limits and usage pricing apply. No Cloudflare resources have been provisioned by merely committing this code.

For local development, copy `push/wrangler.example.jsonc` to ignored `push/wrangler.json`, use a dummy database UUID, set `SITE_ORIGIN` to your test origin and set test-only VAPID keys in ignored `push/.dev.vars`. Run local migrations, then `npx wrangler dev --config push/wrangler.json --test-scheduled`. Local API and SQL tests do not prove delivery to a phone.

## Scheduling, retries and source accuracy

The server reads only the public canonical `site/events.json` from the repository. User requests contain saved IDs/lead times, never trusted event dates or notification text. A failed, invalid, empty or over-three-day-old data snapshot sends nothing until a fresh snapshot is available. Only explicit timezone-aware deadlines with evidence produce jobs. Unknown deadlines remain watched so a newly published deadline can create a reminder without reopening the app. Cancelled, postponed, closed, sold-out and ended races are suppressed. Aliases preserve saved-race matches.

A five-minute cron reconciles 100 subscriptions per tick in a persisted round-robin and delivers up to 25 due alerts. These are initial operational limits, not a claim of unlimited capacity. Queued alerts are checked against the current subscription and latest dataset immediately before sending, so an old deadline or unsaved race is discarded even before its next reconciliation. Delivery keys contain the race, deadline and lead time; atomic leases prevent concurrent cron delivery. Provider acceptance marks sent, transient errors retry with bounded backoff, permanent failures are recorded, and 404/410 removes expired subscriptions. Retry TTL is 30 minutes after the scheduled time, clipped to the deadline for lead-time alerts. A browser receipt store and notification tag reduce duplicate alerts after ambiguous network outcomes. At-least-once network delivery cannot promise exactly-once display.

Jobs expire after that short delivery window. A fresh subscription does not backfill alerts scheduled before opt-in. Pending jobs for changed settings are deleted immediately. Subscriptions unused for 180 days are removed; reopening and syncing refreshes retention. Delivery history expires 30 days after its alert expires. No notification endpoint, token, subscription key or race selection is logged by application code.

Inspect private operational counts with `npx wrangler d1 execute DB --remote --config push/wrangler.json --command "SELECT value FROM state WHERE key='last_run'"`. Track backlog, oldest due time, failed/retry counts and the last successful run. If demand approaches 25 deliveries per five minutes, move delivery to a queue/fan-out design or raise controlled limits on an appropriate Workers plan **before** accepting more volume. No public internal dashboard or recipient list is exposed.

When the Worker serves the website, race/club data proxy the current public repository with a short cache and fall back to bundled assets on fetch failure. Existing Cloudflare Pages deployments retain their own update mechanism. The service worker never caches `/api/` responses. Notification taps open the canonical race details inside Kart Atlas.

## Verify before enabling broadly

- `npm run test:push`: actual SQLite migration/API/scheduler tests, independent decryption of a real encrypted Web Push payload, browser-client permission/sync tests, service-worker push/click tests, and an actual local Cloudflare/D1 runtime smoke test.
- `npm run push:build`: Cloudflare dry-run bundle/config validation; uploads nothing.
- Enable on one Android phone and one Home Screen iPhone. Deliver a controlled, clearly identified test reminder; check foreground/closed-app behavior, permissions denied/granted, tapping into race details, offline reconnect, unsave/mute, changed deadlines and disable/deletion. Never change a real public race deadline just to test.
- Check the last-run counts and actual provider delivery. A successful provider response alone is not proof that a lock-screen alert appeared.

Public data-use details: `/notification-privacy.html`. These describe the feature's storage and controls; they are not a substitute for final store privacy disclosures if native store distribution is resumed.
