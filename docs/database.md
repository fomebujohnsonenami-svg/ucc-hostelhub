# Database and storage setup

Django owns the application schema. The migrations in `backend/apps/` create the tables, and the migration in `backend/common/` locks down PostgreSQL access. Supabase owns Auth and the Storage service. Application CRUD belongs in Django. The frontend reads and writes application data through the Django APIs.

## Relationships

| Tables | Relationship |
| --- | --- |
| `profiles` | One row per Supabase Auth user. The primary key is the verified access token's subject UUID. Django has no cross-schema dependency on Supabase's `auth.users`. |
| `manager_profiles` | One-to-one with a manager profile identity. |
| `hostels`, `hostel_images`, `room_types` | Managers own hostels. A hostel can have ordered photos and multiple room types. |
| `amenities`, `hostel_amenities` | Many-to-many between hostels and amenities. Each hostel and amenity pair is unique. |
| `saved_hostels` | Student-to-hostel favourites. Each pair is unique. |
| `roommate_profiles` | One roommate profile per student. New profiles are private by default. |
| `conversations`, `conversation_participants`, `messages` | Threads have unique participant memberships and messages associated with their sender. Deleting a hostel clears the optional reference and preserves its threads. |
| `subscription_plans`, `manager_subscriptions` | Managers can reference plans over a fixed time interval. Plan records do not trigger payments. |
| `moderation_reports` | A report can retain its history after a reporter is deleted. Target type and UUID identify the reported object across different tables. |

All application primary keys, including association row IDs, are UUIDs. Prices and roommate budgets are decimals in GHS. A room's available beds must be between zero and its total capacity. Indexes support common publication, availability, price, thread history, and moderation queries. Phone numbers, verification notes, and message bodies are private application data.

Django endpoints must enforce profile roles and conversation membership before writing. Foreign keys enforce identity and referential integrity. Django provisions an account profile after Supabase sign-in and onboarding. Registering in Supabase alone does not create a Django profile. Protected APIs use the matching Auth UUID and the Django profile role.

## Connect a Supabase project

1. In Supabase **Connect**, use the direct connection or the session pooler for IPv4-only clients. Use the exact host, port, database, username, and password from the connection panel. Use the same project for PostgreSQL, Auth and Storage.
2. Copy `backend/.env.example` to `backend/.env` for a fresh local configuration. Set `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. Use TLS; for production use `POSTGRES_SSLMODE=verify-full` and set `POSTGRES_SSLROOTCERT` to the trusted CA file when needed.
3. Set `SUPABASE_URL` to the project HTTPS origin. Django verifies asymmetric tokens through the project JWKS. Set `SUPABASE_JWT_SECRET` only for a legacy HS256 project. Set `SUPABASE_SERVICE_ROLE_KEY` to the backend-only legacy service-role key for Storage. Configure a stable `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=false` for deployment. Keep credentials in a private environment store.
4. From `backend/`, with the virtual environment activated, run:

   ```shell
   python -m pip install -r requirements.txt
   python manage.py migrate --noinput
   python manage.py configure_storage
   python manage.py check
   ```

   On Windows PowerShell, use `.\.venv\Scripts\python.exe` in place of `python` if the environment is inactive.

Use a database connection role that owns the Django tables. Apply the migrations before opening application traffic. Disable Supabase's Data API if the project does not use it elsewhere. PostgreSQL RLS is enabled on the application and Django internal tables without allow policies, and privileges for the Supabase API roles and `PUBLIC` are revoked. Keep Django's database role and Storage credentials server-side. Subsequent Django migrations that add tables should apply the same access controls.

## Private Supabase Storage

`configure_storage` creates or updates `hostel-images` and `avatars`, configurable via `SUPABASE_HOSTEL_BUCKET` and `SUPABASE_AVATAR_BUCKET`. It makes both buckets private, limits hosted objects to WebP files up to 5 MiB, and adds bucket-specific restrictive RLS policies to the provider-managed `storage.objects` table. The policies block direct reads and writes by `anon` and `authenticated`, including when another policy is permissive. Run the command using a database role permitted to manage policies on that table. It leaves other buckets' access policies in place.

| Django route | Access |
| --- | --- |
| `POST /api/hostels/<id>/images/` | Owning manager. Multipart file field `image`. Returns the new image UUID and sort order. |
| `GET /api/hostels/<id>/images/<image_id>/` | Signed-in profiles for published listings. Owning manager or admin for unpublished listings. |
| `DELETE /api/hostels/<id>/images/<image_id>/` | Owning manager. |
| `GET`, `PUT`, `DELETE /api/profile/avatar/` | Caller’s own avatar. `PUT` takes a multipart file in the `image` field. |

Each operation uses a Supabase bearer access token. Django checks the token and the database role before sending any privileged Storage request. It decodes the image, rejects invalid or animated content, and re-encodes it as WebP under a server-generated object key. Private images are served through Django. `avatar_storage_path` tracks the managed object independently of the optional `avatar_url`.

Set the deployment's HTTP request body limit slightly above the image limit to allow for multipart framing, for example 6 MiB. Storage operations and PostgreSQL writes are separate transactions. Django attempts to remove an uploaded object if database persistence fails and logs failures to remove unreferenced objects. Include storage cleanup when adding bulk profile or hostel deletion. After provisioning, test upload, retrieval and deletion with real project users, and check that direct public and signed-in Storage access is denied for both buckets.

## Local development and tests

Leave `POSTGRES_HOST` unset for SQLite. To retain local demonstration records, set `SQLITE_PATH` to a local `.sqlite3` file, run `python manage.py migrate`, then run `python manage.py seed_demo`. The default local seed path requires persistent SQLite in DEBUG mode and creates fictional database records. For isolated hosted demonstrations, the command can link confirmed Supabase Auth accounts using an explicit opt-in. See the [deployment guide](deployment.md).

Run `python manage.py makemigrations --check --dry-run` and `python manage.py test` from `backend/`. SQLite runs the schema, API and model tests and skips PostgreSQL-specific policy tests.

Run the full PostgreSQL suite against a disposable local cluster. Create `anon`, `authenticated`, and `service_role` cluster roles, use a database owner that can create test databases and `SET ROLE` to the API roles, and point the `POSTGRES_*` settings at that cluster. The storage policy test creates a stand-in provider table inside the test transaction. Storage HTTP tests mock the provider.
