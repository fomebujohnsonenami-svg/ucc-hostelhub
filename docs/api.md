# Core API and account setup

The frontend uses Django for application data and Supabase for sign-in. Configure `VITE_API_BASE_URL` (ending in `/api`), `VITE_SUPABASE_URL`, and `VITE_SUPABASE_PUBLISHABLE_KEY`. Configure the corresponding project's JWT settings, database connection, and private storage in Django using the [database guide](database.md). Apply all migrations before launching Django, including the default amenities and roommate moderation migrations.

In Supabase Auth, enable the Email and Google providers and configure the callback allowlist. See the [deployment guide](deployment.md) for confirmation and OAuth setup. Use exact frontend origins in Django's CORS settings. Keep the Storage service-role key and database credentials on the server.

## Administrator access

Public onboarding permits student and manager accounts. Provision the first administrator with the verified, server-side `bootstrap_admin` command in the [deployment guide](deployment.md). The administrator signs in normally using the matching Supabase Auth account.

## Workflow and API reference

Endpoints below are relative to `/api/`. Protected calls carry a Supabase bearer token. Django determines identity and role from the token and the corresponding profile. Discovery, public roommate search, and approved photos are public. Application tables remain inaccessible through the Supabase Data API.

| Endpoints | Purpose |
| --- | --- |
| `onboarding/`, `me/` | Provision a profile for a verified user or read and edit their own profile |
| `hostels/`, `hostels/<id>/`, `hostel-filters/`, `amenities/` | Approved discovery and filter options |
| `saved-hostels/`, `saved-hostels/<id>/`, `saved-hostels/ids/` | Student favourites and saved state |
| `manager/hostels/`, `manager/hostels/<id>/`, `manager/hostels/<id>/publication/` | Owner-only listing management |
| `manager/hostels/<id>/rooms/`, `manager/hostels/<id>/rooms/<room>/` | Owner-only room types, semester prices and availability |
| `hostels/<id>/images/`, `hostels/<id>/images/<image>/` | Owner-only photo upload and deletion. Unpublished photos can be read by the owner or admin. |
| `roommates/`, `roommates/<id>/`, `roommates/me/` | Visible roommate matching and the student's own profile |
| `conversations/`, `conversations/<id>/`, `conversations/<id>/messages/`, `conversations/<id>/read/` | Participant-only conversation access, message history, and read position |
| `dashboard/student/`, `dashboard/manager/`, `dashboard/admin/` | Role-scoped database metrics |
| `reports/`, `admin/listings/`, `admin/managers/`, `admin/users/`, `admin/reports/` | Reporting, review, verification, and moderation |

Discovery filters include `q`, `area`, `min`, `max`, `room`, `available=yes`, repeated `amenity`, and `sort=latest|low|high`. Price and availability filters match the same room type. Budget bounds apply to semester prices. Paginated APIs accept `page` and `page_size` and return `count`, `next`, `previous`, and `results`.

New listings wait for review. Approval makes a listing eligible for publication by its owner. A suspended or rejected listing must be submitted and approved again before publishing. Listing and room deletion require JSON `{"confirm":true}`. Capacity is room count times beds per room. Setting available beds records the manager's confirmation time. `AVAILABILITY_STALE_HOURS` defaults to 48. Reported availability is an estimate maintained by the manager.

Roommate ranking awards three points for an overlapping budget, two for a matching area, and one per shared lifestyle preference. Only published, unmoderated roommate profiles are searchable. Messages poll every five seconds. Read requests name the newest message the user has seen, so unseen messages remain unread. Moderators can redact a reported message through its report without reading the conversation history.

OpenStreetMap tiles and external Google Maps directions retain the [map configuration](maps.md). See the [premium guide](premium.md) for plan pricing, featured placement and presentation settings.
