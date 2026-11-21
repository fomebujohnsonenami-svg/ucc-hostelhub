# UCC Hostel Hub QA report

**Audit date** — 21 November 2026

**Result** — Local integration passed. Hosted Supabase and external map services remain unverified.

The audit used Chromium, Django, and a disposable PostgreSQL database. The browser communicated with the real Django endpoints and tested persistent application records. Supabase Auth responses and Storage transport were simulated locally. Leaflet tile responses and the final Google Maps page were stubbed where necessary.

## End-to-end scenarios

| Scenario | Local result |
| --- | --- |
| 1. Manager registration and approval | Registered and onboarded a manager, verified that manager as an administrator, created a listing and room type, uploaded a photo, reviewed the listing, and published it. The owner could preview the pending listing while the public endpoint returned 404. |
| 2. Student registration and discovery | Registered and onboarded a student, filtered by name, area and maximum price, and saw the saved hostel after opening the favourites page. |
| 3. Student and manager messaging | Sent a hostel inquiry and observed the manager’s reply arrive in the student’s open thread through polling. |
| 4. Availability | Changed the reported availability from five to three beds and observed the updated count on the student detail page. |
| 5. Roommate profile and contact | Created two student profiles, found the second student in discovery, and verified receipt of a message in the second student’s thread. |
| 6. Directions | Verified a new tab opened at the Google Maps directions URL with the exact persisted latitude and longitude. External page loading was stubbed. |
| 7. Premium | Opened **Upgrade to Premium**, verified the Coming Soon dialog had no payment inputs or checkout request, and dismissed it with Escape. |
| 8. Unauthorized actions | Verified anonymous writes returned 401, wrong-role mutations returned 403, and nonowners and nonparticipants received 404 for private records. The student UI denied entry to the admin workspace. |

## Frontend checks

- Chromium visited 45 public, student, manager and administrator route variants at 375, 768, 1024 and 1440 px. All 180 route and viewport checks passed without horizontal overflow, uncaught page errors or broken rendered app images.
- Checked public mobile navigation, mobile sidebar navigation and keyboard dismissal. The automated axe WCAG A and AA scan found no violations on 19 representative routes at 375 px. This was a scoped automated scan.
- Verified initial empty discovery, loading feedback during a delayed request, a visible API error when that request failed, and a readable fallback when a listing photo failed to load.
- Supplemental browser checks covered password reset requests and password updates with simulated Auth, persisted profile changes, API health feedback, grid/list/map controls, keyboard marker activation, student reporting, administrator review, and logout.
- ESLint, TypeScript checking, and the Vite production build passed.

## Backend checks

- Successfully connected to local PostgreSQL and applied all migrations on a fresh database. Django system checks, the applied migration check and the migration drift check passed.
- All 39 Django tests passed on PostgreSQL. SQLite passed 36 tests and skipped the three PostgreSQL-only policy tests.
- The suite covered token validation, API response contracts, ownership, image operations, PostgreSQL row-level policies, availability, roommate privacy, message authorization, and administrator moderation.

## Fixes made during the audit

- Added the missing manager **Upgrade to Premium** action and shared its payment preview with public pricing.
- Routed owner listing previews through the protected manager API so a manager can view a draft and its photos before publication.
- Corrected the sign-up username pattern, prevented Escape from dismissing a dialog when its owner is handling a pending operation, and added fallbacks for failed gallery and card images.
- Added request body validation and a regression test for action endpoints that previously assumed JSON was an object.

## External checks still open

- The workspace has no live Supabase connection or project credentials. Hosted PostgreSQL, real Auth signup and confirmation emails, OAuth, password reset delivery, and live Storage upload, download, and policy behavior remain unverified.
- The workspace proxy denied outbound connections to OpenStreetMap tiles and the Google Maps directions URL. Check actual tiles and the external Google Maps page in a browser with outbound access.
- Payment processing remains outside the application. The audit verified the Coming Soon experience.
