# UCC Hostel Hub

UCC Hostel Hub helps University of Cape Coast students find accommodation and roommates. React uses Django REST Framework for listings, availability, favourites, messaging, moderation, and dashboard metrics. Supabase provides Auth, PostgreSQL, and private Storage. See the [API guide](docs/api.md) and [database setup](docs/database.md).

## Project structure

| Path | Purpose |
| --- | --- |
| `frontend/public/images/` | Public image assets |
| `frontend/src/` | React pages, layouts, routes, API utilities, and Tailwind theme |
| `backend/config/` | Django settings, routing, and ASGI/WSGI entry points |
| `backend/apps/` | Django modules for accounts, hostels, roommates, messaging, subscriptions, and moderation |
| `backend/common/` and `backend/tests/` | Shared API views and tests |
| `docs/` and `scripts/` | Reserved for documentation and project automation |

## Windows PowerShell setup

Install Git, Python 3.12, and Node.js 22.13 or newer in the Node 22 series, or Node.js 24 or newer. Open two PowerShell terminals at the repository root.

### Backend

```powershell
Set-Location backend
py -3.12 -m venv .venv
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SQLITE_PATH = "dev.sqlite3" # Local only. Omit when POSTGRES_HOST is configured.
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py runserver localhost:8000
```

The explicit virtual environment executable avoids changing PowerShell's execution policy. Copy the example only when creating a fresh local configuration. For a hosted database or private photo storage, configure the [Supabase settings](docs/database.md) before starting Django.

### Frontend

```powershell
Set-Location frontend
Copy-Item .env.example .env
npm.cmd ci
npm.cmd run dev
```

Open `http://localhost:5173` to explore the application. To verify Django from the browser, open **Help & Support** and select **Check Django connection**. The page displays **API connection verified** after Django returns HTTP 200 with `{"status":"ok"}` from `/api/health/`. The health check verifies the HTTP connection to Django and does not query a database. If the connection fails, check the Django terminal, the frontend API base URL, and the exact frontend origin in the backend CORS setting. Restart the relevant server after editing its environment file.

On Linux and macOS, use `python3 -m venv .venv`, `.venv/bin/python`, `cp`, and `npm` in place of their PowerShell counterparts.

## First accounts and listings

- Set the frontend Supabase project URL and public browser key, and configure the matching backend token verification. Follow the [API guide](docs/api.md).
- Register and confirm a student or manager account. Finish onboarding to create the Django profile. Bootstrap an administrator using the trusted server procedure in the API guide.
- A manager submits a listing for review. An administrator approves it, then the owner publishes it.
- In local SQLite development, run `python manage.py seed_demo` to create labelled database fixtures. Those records do not sign in with Supabase. The site's hero image is illustrative.
- Payment checkout remains a preview.

## Configuration

Public browsing works locally after setting a persistent SQLite path and applying migrations. Signed-in flows require the Supabase configuration.

- Frontend `VITE_API_BASE_URL` is the API root including `/api`. Vite exposes all `VITE_` values to the browser. Keep database passwords, Django secrets, and the Supabase service-role key in server-side configuration.
- Backend `CORS_ALLOWED_ORIGINS` and `DJANGO_ALLOWED_HOSTS` accept comma-separated lists. The defaults allow local development on `localhost` and `127.0.0.1`.
- With `DJANGO_DEBUG=true` and `POSTGRES_HOST` empty, Django uses in-memory SQLite for local scaffolding. To select PostgreSQL, configure the `POSTGRES_*` values using the Supabase Connect panel. For an IPv4 environment, use the Supabase session pooler and its matching user and port. The default SSL mode is `require`.
- With `DJANGO_DEBUG=false`, provide `DJANGO_SECRET_KEY`, an explicit host and origin configuration for the deployment, and the PostgreSQL connection settings. Keep real values in an ignored local `.env` or a private environment-variable store.

## Validation

From `frontend/`:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

From `backend/`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

The Django suite covers model constraints, bearer-token verification, discovery, availability, messaging authorization, role permissions, image operations, dashboard metrics, and moderation. See the [database guide](docs/database.md) for PostgreSQL policy tests and migrations.

## Interactive hostel maps

Find Hostels includes a Leaflet Map View for approved live listings with saved coordinates. See the [maps guide](docs/maps.md) for manager sign-in, tile configuration, and deployment checks.

## Premium plans

See the [premium presentation guide](docs/premium.md) for pricing, presentation flags, and the manager promotion workflow.

## Deployment and university presentation

- [Deployment guide](docs/deployment.md)
- [User manual](docs/user-manual.md)
- [Demonstration script](docs/presentation-script.md)
- [Feature checklist](docs/feature-checklist.md)
- [Technical architecture](docs/architecture.md)
- [Troubleshooting](docs/troubleshooting.md)
