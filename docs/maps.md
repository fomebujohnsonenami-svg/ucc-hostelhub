# Hostel maps

The directory and detail pages read approved listings from Django. A public listing must have both `verification_status=verified` and `publication_status=published`. Grid and Map View use the same filtered results page. Only listings with a valid coordinate pair appear as markers.

The map centers on the UCC area if there are no markers. The details page uses the saved coordinates for its pin and Google Maps directions link. That link opens a separate site and uses no Google API or key.

## Connect a live manager account

1. Follow the [database setup guide](database.md) to configure Supabase PostgreSQL, Auth and Django. The existing coordinate fields are nullable decimals with six fractional digits. No map migration is needed beyond the existing Django migrations.
2. Set `VITE_API_BASE_URL` to the Django API root for local development. Keep service-role and database credentials on the backend.
3. Sign in with a Supabase account and open **Manager → My Hostels**. Sign-in and onboarding create a Django `Profile` and `ManagerProfile` for new manager accounts. The form uses the Supabase session bearer token.
4. Use **Add Hostel** or **Edit Hostel**. Click the map, drag the marker, or type both coordinates. Saving a new listing creates a pending record. An administrator approves the listing, then the owner publishes it from **My Hostels**.

Django exposes public read-only listing routes at `/api/hostels/` and `/api/hostels/<uuid>/`. The photos route under a listing proxies only approved listing photos from private Supabase Storage. The owner-only endpoints `/api/manager/hostels/` and `/api/manager/hostels/<uuid>/` use GET, POST for creation, and PATCH for edits. Django derives ownership from the verified session. A coordinate pair may be absent or cleared together. Latitude must be in −90 to 90 and longitude in −180 to 180.

## Tile provider

For a small university demonstration the default raster URL is `https://tile.openstreetmap.org/{z}/{x}/{y}.png`. Leaflet requests tiles for the visible map as the user pans and zooms. The map displays linked OpenStreetMap attribution and leaves normal browser HTTP caching and referrer behavior in place. Follow the [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/). Public tiles are shared infrastructure without a production service guarantee.

To use another OpenStreetMap-compatible raster provider, set `VITE_MAP_TILE_URL` and `VITE_MAP_TILE_ATTRIBUTION` together in the frontend environment. Keep all attribution required by the provider and by OpenStreetMap. Attribution strings are trusted deployment configuration and can contain attribution links. Restart Vite or rebuild the production frontend after changing these values. If outbound access or Content Security Policy is restrictive, permit tile image requests to the configured tile host and API requests to Django and Supabase. For larger deployments, choose a hosted OpenStreetMap tile service with suitable traffic limits and support, or operate your own tile infrastructure.

Run `npm run lint`, `npm run typecheck`, and `npm run build` in `frontend/`, and `python manage.py test` in `backend/`. To verify a deployment, compare public markers against stored coordinates, apply filters, check the directions URL, and try saving and reloading a location with an authorized manager. A second manager must be unable to edit the same listing.
