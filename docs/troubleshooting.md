# Troubleshooting

| Symptom | Check |
| --- | --- |
| Vercel returns 404 on a page refresh | Confirm **Root Directory** is `frontend` and the deployment includes `frontend/vercel.json`. Verify the output directory is `dist`. |
| Django returns 400 or rejects a health probe | Verify the request hostname is listed in `DJANGO_ALLOWED_HOSTS`. Check the health endpoint path and distinguish web health from database readiness. |
| Requests are blocked by CORS | Match the browser’s exact HTTPS origin in `CORS_ALLOWED_ORIGINS`. Confirm `VITE_API_BASE_URL` ends in `/api`, then rebuild the frontend. |
| HTTPS redirect loops | Confirm the hosting edge sets `X-Forwarded-Proto: https`. Enable `DJANGO_TRUST_PROXY_HTTPS` only behind an edge that overwrites the header and protects the origin. |
| PostgreSQL connection or certificate error | Check the direct connection or session pooler values in Supabase **Connect**. Confirm the CA file is readable, the hostname matches, and the configured user owns the Django tables. Keep `verify-full` enabled. |
| Discovery returns a server error | Confirm `python manage.py migrate --check` succeeds in the deployed backend environment. Review service logs for database errors. |
| Signup does not open onboarding | Check that Email and new user signups are enabled and Confirm email is off in Supabase. Check the runtime logs if the profile API returns an error. |
| Sign-in succeeds but the dashboard stays closed | Verify profile onboarding completed and the Django project matches the Supabase browser project. The route must match the role on the Django profile. |
| Photo upload or loading fails | Confirm the private buckets are configured and the backend service role is set. Use a valid still JPEG, PNG or WebP under 5 MiB. Review the HTTP request size limit and backend logs. |
| Map has no pins or tiles | Pins need stored coordinates on approved, published listings. Check exact filters, browser network access and tile provider configuration. The demo directions point belongs to Demo Atlantic View Hostel. |
| Demo seed command refuses to run | Use persistent SQLite in debug mode for local browsing. Hosted seeding requires a dedicated PostgreSQL presentation project, both backend flags, three distinct confirmed Auth users, and fresh or matching demo profiles. |
| Browser build rejects the Supabase key | Use the project's public publishable key or legacy anon key. Keep service-role and signing keys on the backend. |

Use the [deployment guide](deployment.md) for the complete environment and release sequence.
