# Deployment guide

Deploy the React frontend to Vercel and run Django as a separate Python web service. These instructions use Render for the Django service. Supabase supplies PostgreSQL, Auth and private Storage. Use a dedicated Supabase project for the fictional presentation data.

## 1. Configure Supabase

1. Create the presentation project. In **Connect**, select the direct PostgreSQL connection if the backend host supports its network requirements, or the session pooler for IPv4. Copy the exact host, port, database and username from that panel.
2. Obtain the trusted CA certificate for the chosen database endpoint. Configure libpq with `verify-full` and the CA path to verify both the certificate and hostname. Keep the database password and server-only Supabase key in the backend host’s secret settings.
3. In Supabase Auth, enable email/password and set **Site URL** to the actual HTTPS frontend origin. Add the production callback paths to **Redirect URLs**. Allow `https://FRONTEND_HOST/login**` on the exact trusted frontend hostname for the app’s role and return-path query parameters, and `https://FRONTEND_HOST/set-password` for password recovery. Replace `FRONTEND_HOST` with the hostname Vercel assigns or the attached custom domain.
4. For Google sign-in, create a Google OAuth **Web application** and configure its consent screen. In **Authorized redirect URIs**, paste the exact Supabase Auth callback shown on the Google provider settings page, typically `https://PROJECT_REF.supabase.co/auth/v1/callback`. Paste the Google client ID and secret into Supabase’s Google provider settings. If the consent screen is in testing, add your presenter’s Google account as a test user.
5. After Django is configured, run `python manage.py configure_storage` from a trusted environment connected to the hosted database. It creates or configures the private hostel and avatar buckets and their access policies. See the [database guide](database.md).

## 2. Configure the Django web service

Create a Python web service from the repository, with **Root Directory** set to `backend`. The repository root directory must contain the project files on the deployment branch.

| Setting | Value |
| --- | --- |
| Python | 3.12 |
| Build | `python -m pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| Start | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --access-logfile -` |
| Health check | `/api/health/` |
| One-off release step | `python manage.py migrate --noinput && python manage.py migrate --check` |

Provide the environment variables before the first build. Run the release step as a pre-deploy command on a plan that supports it, or manually from an authorized one-off shell with the same production environment. Finish migrations before sending traffic to the service. The backend ships a [Procfile](../backend/Procfile) for hosts that use one. Gunicorn serves Django, and WhiteNoise serves collected, hashed static assets.

| Backend variable | Production value |
| --- | --- |
| `DJANGO_ENV`, `DJANGO_DEBUG` | `production`, `false`. The production environment forces debug off. |
| `DJANGO_SECRET_KEY` | A unique high-entropy value stored only as a backend secret. |
| `DJANGO_ALLOWED_HOSTS` | The exact public backend hostname, plus any separate hostname actually used by the hosting provider’s health probe. Use hostnames without schemes. |
| `CORS_ALLOWED_ORIGINS` | The exact HTTPS Vercel or custom frontend origins. Use a comma-separated list for multiple origins. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Exact HTTPS origins for any cross-origin cookie-based Django forms. The current React API uses bearer tokens. Leave this empty if no such forms are deployed. |
| `DJANGO_TRUST_PROXY_HTTPS` | Set `true` only on a trusted HTTPS-terminating edge that sets or replaces `X-Forwarded-Proto` and prevents direct access to Gunicorn. |
| `DJANGO_HSTS_SECONDS` | Defaults to one year in production. Enable `DJANGO_HSTS_INCLUDE_SUBDOMAINS` and `DJANGO_HSTS_PRELOAD` only after confirming the domain policy and HTTPS coverage. |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Exact Supabase values, stored securely. |
| `POSTGRES_SSLMODE`, `POSTGRES_SSLROOTCERT` | `verify-full` and the trusted CA file’s absolute path. Render secret files can mount the CA under `/etc/secrets/`. |
| `SUPABASE_URL` | HTTPS project origin, without a path. |
| `SUPABASE_JWT_SECRET` | Leave empty for the project's asymmetric signing keys. Supply privately only for a legacy HS256 project. |
| `SUPABASE_SERVICE_ROLE_KEY` | The backend-only legacy service-role key used by Storage and operator Auth checks. |
| `PRESENTATION_MODE` | `true` for the presentation. |
| `DEMO_SEED_ENABLED` | Keep `false`; enable briefly only when loading the isolated presentation database. |

Check that HTTPS responses work through the hosting proxy, then run `python manage.py check --deploy`. A local production settings check cannot establish the provider's actual TLS and forwarding behavior. The health endpoint checks the web process. Use `migrate --check` and a real listing API request to verify database access.

## 3. Configure Vercel

Import the project using **Root Directory** `frontend`, framework **Vite**, Node 22 or 24, install command `npm ci`, build command `npm run build`, and output directory `dist`. The included [Vercel configuration](../frontend/vercel.json) provides SPA deep links and basic headers.

Set these values in Vercel’s environment settings and rebuild.

- `VITE_API_BASE_URL` — Actual HTTPS backend origin with `/api` appended.
- `VITE_SUPABASE_URL` — Same project origin as Django.
- `VITE_SUPABASE_PUBLISHABLE_KEY` — Public browser key or legacy anon key.
- `VITE_PRESENTATION_MODE=true` — Show presentation labels.
- `VITE_MAP_TILE_URL` and `VITE_MAP_TILE_ATTRIBUTION` — Optional tile provider overrides. See the [maps guide](maps.md).

Vite embeds these values in browser bundles. Keep every database, Auth signing, storage service-role and Google OAuth secret out of Vercel’s `VITE_` variables. Update Supabase callbacks and Django origins if the frontend domain changes.

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
