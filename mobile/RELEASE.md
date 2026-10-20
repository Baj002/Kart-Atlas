# Kart Atlas mobile release preparation

Status: unsigned release candidates; no store upload or publication is automated.

## Reproduce the mobile projects

Use Node 22+, Python 3.12+ and `pip install -r mobile/requirements.txt`.

```
npm ci
npm run mobile:sync
npm run test:mobile
```

The pinned Capacitor 8.5.3 templates generate `android/` and `ios/`. `mobile/configure-platforms.py` applies the version, brand icons, notification icon, disabled Android cloud backup and iOS privacy manifest. Both generated folders are ignored: make durable native changes in the configuration script, not an untracked generated project. The committed lockfile and scripts reproduce these projects.

`mobile-release.yml` builds an installable Android debug APK, an **unsigned** Android release AAB and an **unsigned** iOS device archive. Download them from the workflow's artifacts. An unsigned archive is not an App Store IPA. The debug APK is for testing, not a Google Play release. No store credentials are embedded or requested by this workflow.

Android uses JDK 21, compile/target API 36 and minimum API 24. iOS uses Xcode 26 or newer and a minimum deployment target of iOS 15. The workflow uses the macOS 26 runner. Current requirement sources checked October 20, 2026:
- https://capacitorjs.com/docs/updating/8-0
- https://developer.apple.com/news/upcoming-requirements/?id=04282026a
- https://support.google.com/googleplay/android-developer/answer/11926878

## Product behavior

Application code and an initial public directory are bundled, so the app is more than a remote website view. Leaflet assets ship locally. Race/club data refresh from the public repository and fall back to a local cache or bundled snapshot. No internal coverage pages, reports or source inventories are packaged. Registration sites open in a system browser session. Calendar and overview exports use native file sharing. Android back closes a dialog before navigating or exiting.

Phone reminders are explicitly enabled by the user. Pending alerts are reconciled on saved-race or reminder changes and when the app refreshes/resumes. Removed, muted, cancelled, postponed or closed races lose pending alerts. Deadline changes replace old alerts. Up to 60 future alerts are scheduled to leave room below iOS's pending-notification limit. Android uses inexact scheduling and does not request exact-alarm access. Permission or battery restrictions may delay delivery. With no background data-fetch service, reminders use the last synced deadline while closed; the interface explains that users must reopen to refresh changes.

## Submission gate

`npm run release:check` intentionally fails until the owner confirms the fields in `mobile/release.json`: publisher identity, support email, public privacy policy URL, identifier, privacy disclosures and real-device QA. `com.baj002.kartatlas` is a proposed identifier, not a claimed or registered store identity. Keep the developer accounts and signing credentials under the owner's control. Never commit keystores, passwords, certificates or provisioning profiles.

After those confirmations, generate signing keys/profiles in the owner's accounts, sign the Android AAB and export the iOS archive with the appropriate team and provisioning. Use the native projects for signed builds; no unsigned build should be labelled store-ready.

## Physical-device acceptance

Test on an Android phone and iPhone before asserting release readiness:
- Cold launch, airplane-mode launch, cache fallback and a real online dataset refresh.
- Search, map tiles, monthly calendar and club-directory navigation, including Android back.
- Save/unsave persistence across process termination and safe-area/keyboard layouts.
- Notification permission denied/granted, alert delivery with the app closed, changed deadlines, cancellation and disabling reminders.
- External registration login/payment pages, returning to Kart Atlas and sharing both ICS and HTML files.
- VoiceOver/TalkBack, large text and portrait/landscape layouts.

Capture actual device screenshots after this pass. Draft store copy and privacy disclosure facts are in `mobile/store/`. Publish the owner-approved privacy policy at a public HTTPS URL and put that URL in the store listings. New personal Google Play accounts may also need the required closed testing period before production access.
