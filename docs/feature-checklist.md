# Feature checklist

## Locally verified

| Feature | Evidence |
| --- | --- |
| Landing, navigation and responsive student, manager and administrator pages | QA used Chromium at 375, 768, 1024 and 1440 px. |
| Public hostel search, price and area filters, saved hostels and listing details | Django and browser integration checks. |
| Map markers and directions | Leaflet behavior tested with fixture tiles. Directions opened a new tab using the stored coordinates. |
| Account onboarding and role authorization | Django validated tokens against local fixtures. Browser exercised sign-up and subsequent onboarding using simulated Auth. |
| Roommate discovery, private participant messaging and manager replies | Browser integration exercised both kinds of message threads. |
| Manager availability, approval, draft preview and featured placement | Local Django tests and browser flows. |
| Photo upload and display | Browser exercised Django upload and retrieval with simulated Storage transport. |
| Premium pricing and Coming Soon modal | Verified the student and manager plans and the modal. No payment was processed. |
| Administrator reviews and moderation | Automated role and moderation checks and browser review flows. |
| Presentation dataset | The seeder provides five labelled, fictional listings, multiple room types and example conversations. |

See the [QA report](qa-report.md) for methods and scope.

The deployment rehearsal passed in Chromium against a freshly migrated local PostgreSQL database. It used the seeded dataset, simulated Supabase Auth and Storage, and checked the directions URL. The PostgreSQL test suite passed all 43 tests. Local Gunicorn and WhiteNoise checks passed for HTTPS redirects, exact CORS origins, rejected hosts, health responses and hashed static assets. The production frontend build passed a scan for common server-only credential markers, and the build guard rejected a synthetic server key.

## Hosted acceptance

- [ ] Production migrations and verified TLS connection to Supabase PostgreSQL.
- [ ] Vercel page loads, SPA deep-link refresh and restricted cross-origin API access.
- [ ] Real Google sign-in and first administrator sign-in.
- [ ] Confirmed demonstration users sign in with their hosted Auth accounts.
- [ ] Real Storage upload, photo display and rejection of unauthorized photo writes.
- [ ] OpenStreetMap tiles and Google Maps directions load from the presenter’s browser.
- [ ] All steps in the [demonstration script](presentation-script.md) pass on the deployed application.
- [ ] Review the deployment branch, build logs and browser bundle for accidental credentials.
