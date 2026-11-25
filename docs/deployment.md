# Deployment guide

Use **one Vercel project** for React and Django. Supabase provides PostgreSQL and Storage. Django handles email and password sign-in. Set the Vercel project **Root Directory** to the repository root and let [the root configuration](../vercel.json) control the build. Requests under `/api/` go to the Python function. The rest of the site serves the React build, including deep links.

## 1. Configure Supabase

1. Create the presentation project. In **Connect**, select the direct PostgreSQL connection if the backend host supports its network requirements, or the session pooler for IPv4. Copy the exact host, port, database and username from that panel.
2. Obtain the trusted CA certificate for the chosen database endpoint. Configure libpq with `verify-full` and the CA path to verify both the certificate and hostname. Keep the database password and server-only Supabase key in the backend host’s secret settings.
3. Sign-in uses Django. You can disable **Google**, **Email**, and custom SMTP in Supabase Authentication if the project is dedicated to Hostel Hub. Existing Supabase Auth sessions and passwords are not imported.
4. After Django is configured, run `python manage.py configure_storage` from a trusted environment connected to the hosted database. It creates or configures the private hostel and avatar buckets and their access policies. See the [database guide](database.md).

## 2. Configure Vercel

Import the GitHub repository, leave **Root Directory** at the repository root, and select **Other** as the framework preset. Use Node 22 or 24. The root `vercel.json` builds the frontend and Python function explicitly. Clear any dashboard build or output overrides.

Set these in **Vercel → Project → Settings → Environment Variables** for Production.

| Variable | Production value |
| --- | --- |
| `DJANGO_ENV`, `DJANGO_DEBUG` | `production`, `false` |
| `DJANGO_SECRET_KEY` | A unique high-entropy secret |
| `DJANGO_ALLOWED_HOSTS` | Exact production hostname, without a scheme |
| `CORS_ALLOWED_ORIGINS` | Exact HTTPS production origin |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Exact HTTPS production origin when needed for Django forms |
| `DJANGO_TRUST_PROXY_HTTPS` | `true` behind the Vercel HTTPS edge |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Supabase connection values. Use the session pooler if you need IPv4. |
| `POSTGRES_SSLMODE`, `POSTGRES_SSLROOTCERT` | `verify-full` and a CA path. For a certificate trusted by the runtime’s system bundle, use `/etc/ssl/certs/ca-certificates.crt`. If the endpoint requires a different CA, paste the trusted CA PEM for that endpoint into `POSTGRES_SSLROOTCERT_PEM`. Django writes it to a temporary file and uses it instead of `POSTGRES_SSLROOTCERT`. |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Project HTTPS origin and backend-only legacy service-role key |
| `PRESENTATION_MODE`, `VITE_PRESENTATION_MODE` | `true` for the presentation |
| `VITE_API_BASE_URL` | Leave unset. The production frontend uses the same-origin `/api`. |

Keep secrets in variables without the `VITE_` prefix. Django uses JSON responses. Vercel serves the React static assets. Keep upload requests below Vercel’s 4.5 MB function request limit, including multipart overhead. Use a photo under 4 MB for the demo.

## 3. Run the release commands

With the production backend values loaded in a trusted terminal, change into `backend/` and install its Python requirements. Run these one-off commands before using the API. Vercel function requests do not run migrations.

```bash
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py configure_storage
```

## 4. Provision the administrator and presentation users

Create the intended administrator through the app and record the email and username. From a trusted backend terminal, explicitly promote that account. Sign in again afterward.

```bash
python manage.py bootstrap_admin --email ADMIN_EMAIL --username ADMIN_USERNAME --promote-existing
```

For a hosted presentation, register three accounts through the app using the reserved names and usernames below. Use email addresses you control and distinct passwords.

| Name | Username | Role |
| --- | --- | --- |
| Demo Manager | demo-manager | Manager |
| Demo Student | demo-student | Student |
| Demo Roommate | demo-peer | Student |

Find their profile UUIDs in Supabase’s `profiles` table. Enable `DEMO_SEED_ENABLED=true` and `PRESENTATION_MODE=true` in the seeding terminal, then run:

```bash
python manage.py seed_demo --manager-profile-id MANAGER_UUID --student-profile-id STUDENT_UUID --peer-profile-id PEER_UUID
```

For local browsing, use `DJANGO_DEBUG=true`, leave `POSTGRES_HOST` unset, use a persistent file such as `SQLITE_PATH=demo.sqlite3`, and run migrations and `python manage.py seed_demo`. Those fixture profiles have no login credentials. You can create separate student and manager accounts in the app for a local demo.

## 5. Verify the hosted deployment

- Browse the actual Vercel URL and reload a deep link such as `/hostels` and `/pricing`. In **Help & Support**, run **Check Django connection** and verify discovery also queries the database.
- Check the production frontend origin is allowed and another origin receives no CORS permission. Verify HTTPS and confirm the service is running with debug off.
- Test signup and password sign-in for both roles. Sign out and verify logged-out access behavior. Check the presentation administrator can open the admin dashboard.
- Upload a fictional photo as the demo manager, verify it renders in the approved listing, and verify a different manager cannot modify it. Check the Storage buckets are private.
- Rehearse the [presentation script](presentation-script.md) in the deployed browser. Confirm maps and directions load there. Check the premium modal without entering any payment details.
- Before pushing, review the staged diff and scan with your Git host’s secret-scanning feature if available. Confirm local `.env` files and private keys are ignored. Inspect the production bundle for server-only material before publishing.

The URLs, production health, account login, Storage and hosted workflows remain pending until the project and credentials are connected. See [troubleshooting](troubleshooting.md) if validation fails.
