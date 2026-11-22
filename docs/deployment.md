# Deployment guide

Use **one Vercel project** for React and Django. Supabase provides PostgreSQL, Auth and Storage. Set the Vercel project **Root Directory** to the repository root and let [the root configuration](../vercel.json) control the build. Requests under `/api/` go to the Python function. The rest of the site serves the React build, including deep links.

## 1. Configure Supabase

1. Create the presentation project. In **Connect**, select the direct PostgreSQL connection if the backend host supports its network requirements, or the session pooler for IPv4. Copy the exact host, port, database and username from that panel.
2. Obtain the trusted CA certificate for the chosen database endpoint. Configure libpq with `verify-full` and the CA path to verify both the certificate and hostname. Keep the database password and server-only Supabase key in the backend host’s secret settings.
3. In Supabase Auth, enable email/password and set **Site URL** to the actual HTTPS frontend origin. Add the production callback paths to **Redirect URLs**. Allow `https://FRONTEND_HOST/login**` on the exact trusted frontend hostname for the app’s role and return-path query parameters, and `https://FRONTEND_HOST/set-password` for password recovery. Replace `FRONTEND_HOST` with the hostname Vercel assigns or the attached custom domain.
4. For Google sign-in, create a Google OAuth **Web application** and configure its consent screen. In **Authorized redirect URIs**, paste the exact Supabase Auth callback shown on the Google provider settings page, typically `https://PROJECT_REF.supabase.co/auth/v1/callback`. Paste the Google client ID and secret into Supabase’s Google provider settings. If the consent screen is in testing, add your presenter’s Google account as a test user.
5. After Django is configured, run `python manage.py configure_storage` from a trusted environment connected to the hosted database. It creates or configures the private hostel and avatar buckets and their access policies. See the [database guide](database.md).

## 2. Configure Vercel

Import the GitHub repository, leave **Root Directory** at the repository root, and select **Other** as the framework preset. Use Node 22 or 24. The root `vercel.json` builds the frontend and Python function explicitly. Clear any dashboard build or output overrides.

Set these in **Vercel → Project → Settings → Environment Variables** for Production.

| Variable | Production value |
| --- | --- |
| `DJANGO_ENV`, `DJANGO_DEBUG` | `production`, `false` |
| `DJANGO_SECRET_KEY` | A unique high-entropy secret |
| `DJANGO_ALLOWED_HOSTS` | Exact production hostname, without a scheme |
| `CORS_ALLOWED_ORIGINS` | Exact HTTPS production origin |
| `DJANGO_TRUST_PROXY_HTTPS` | `true` behind the Vercel HTTPS edge |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Supabase connection values. Use the session pooler if you need IPv4. |
| `POSTGRES_SSLMODE`, `POSTGRES_SSLROOTCERT` | `verify-full` and a CA path. For a certificate trusted by the runtime’s system bundle, use `/etc/ssl/certs/ca-certificates.crt`. If the endpoint requires a different CA, paste the trusted CA PEM for that endpoint into `POSTGRES_SSLROOTCERT_PEM`. Django writes it to a temporary file and uses it instead of `POSTGRES_SSLROOTCERT`. |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Project HTTPS origin and backend-only legacy service-role key |
| `SUPABASE_JWT_SECRET` | Leave empty for asymmetric JWT signing. Set it privately only for legacy HS256. |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY` | Same Supabase project origin and its public browser key |
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

Create or invite the intended administrator in the configured Supabase Auth project. Confirm the account and copy its Auth UUID. Give administrator access using Django’s privileged management command from the backend service environment.

```bash
python manage.py bootstrap_admin --auth-id ADMIN_AUTH_UUID --username presentation-admin --full-name 'Presentation Administrator'
```

The command looks up the confirmed Auth user in the configured project. It will only change the role of an existing non-admin profile when the trusted operator also supplies `--promote-existing`. Keep the administrator’s sign-in credentials private.

For the presentation, create three separate confirmed Auth users for Demo Manager, Demo Student and Demo Roommate in the isolated project. Keep their credentials in a password manager. Use fresh accounts that have no Django profiles or already match the reserved demo profiles. Enable `DEMO_SEED_ENABLED=true` for the seeding operation only, then restore it to `false`.

```bash
python manage.py seed_demo --manager-auth-id MANAGER_AUTH_UUID --student-auth-id STUDENT_AUTH_UUID --peer-auth-id ROOMMATE_AUTH_UUID
```

The command verifies the three Auth accounts but does not create their passwords or Auth identities. It loads five labelled fictional listings, ten room types, two roommate profiles and three sample conversations. A public UCC-area reference point on the first listing demonstrates directions. The fictional listing is not a real property. Upload a licensed or fictional image through the demo manager’s photos page after Storage is configured.

For public browsing locally, set `SQLITE_PATH=demo.sqlite3`, run migrations and run `python manage.py seed_demo` with no arguments. Those local profiles cannot sign in through Supabase.

## 5. Verify the hosted deployment

- Browse the actual Vercel URL and reload a deep link such as `/hostels` and `/pricing`. In **Help & Support**, run **Check Django connection** and verify discovery also queries the database.
- Check the production frontend origin is allowed and another origin receives no CORS permission. Verify HTTPS and confirm the service is running with debug off.
- Complete Google sign-in and profile onboarding using a permitted Google account. Sign out and verify logged-out access behavior. Check the presentation administrator can open the admin dashboard.
- Upload a fictional photo as the demo manager, verify it renders in the approved listing, and verify a different manager cannot modify it. Check the Storage buckets are private.
- Rehearse the [presentation script](presentation-script.md) in the deployed browser. Confirm maps and directions load there. Check the premium modal without entering any payment details.
- Before pushing, review the staged diff and scan with your Git host’s secret-scanning feature if available. Confirm local `.env` files and private keys are ignored. Inspect the production bundle for server-only material before publishing.

The URLs, production health, OAuth, Storage and hosted workflows remain pending until the project and credentials are connected. See [troubleshooting](troubleshooting.md) if validation fails.
