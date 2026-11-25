# Core API and account setup

Django manages accounts and API access. Supabase supplies PostgreSQL and private Storage. Configure the backend using the [database guide](database.md) and apply migrations before launching Django.

Call `auth/register/` with email, password, full name, username, role, and a business name for managers. Public registration accepts student and manager roles. Call `auth/login/` with email and password. Both return a session token to send as `Authorization: Bearer TOKEN` on protected requests. `auth/logout/` revokes the current token. Use the [deployment guide](deployment.md) to provision administrators.

## Administrator access

Public onboarding permits student and manager accounts. Provision the first administrator with the verified, server-side `bootstrap_admin` command in the [deployment guide](deployment.md). The administrator signs in normally using the matching Supabase Auth account.

## Workflow and API reference

Endpoints below are relative to `/api/`. Protected calls carry a Supabase bearer token. Django determines identity and role from the token and the corresponding profile. Discovery, public roommate search, and approved photos are public. Application tables remain inaccessible through the Supabase Data API.

| Endpoints | Purpose |
| --- | --- |
| `auth/register/`, `auth/login/`, `auth/logout/`, `me/` | Register, sign in, sign out, and read or edit your profile |
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
