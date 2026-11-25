# Hostel maps

The directory and detail pages read published listings from Django. Suspended or rejected listings stay hidden. Grid and Map View use the same filtered results page. Only listings with a valid coordinate pair appear as markers.

The map centers on the UCC area if there are no markers. The details page opens with a map centered on the saved hostel coordinates. Its Google Maps link opens a separate site and uses no Google API key.

## Walking directions

Visitors can select **Get walking directions** on a hostel listing. The browser asks for permission to use their current location. If granted, the browser sends the origin and hostel coordinates to the [OSRM foot routing service](https://routing.openstreetmap.de/) and draws the returned route on the map. Distance and estimated walking time come from that route. Hostel Hub does not store the visitor’s location. If routing or geolocation fails, visitors can still open the saved hostel location in Google Maps.

## Connect a live manager account

1. Follow the [database setup guide](database.md) to configure Supabase PostgreSQL and Django. The existing coordinate fields are nullable decimals with six fractional digits. No map migration is needed beyond the existing Django migrations.
2. Set `VITE_API_BASE_URL` to the Django API root for local development. Keep service-role and database credentials on the backend.
3. Sign in to Hostel Hub with a manager account and open **My Hostels**. The form uses the Django session bearer token.
4. Use **Add Hostel** or **Edit Hostel**. Click the map, drag the marker, type both coordinates, or opt to use your current location. Saving a new listing publishes it immediately.

Django exposes public read-only listing routes at `/api/hostels/` and `/api/hostels/<uuid>/`. The photos route under a listing proxies only published listing photos from private Supabase Storage. The owner-only endpoints `/api/manager/hostels/` and `/api/manager/hostels/<uuid>/` use GET, POST for creation, and PATCH for edits. Django derives ownership from the verified session. A coordinate pair may be absent or cleared together. Latitude must be in −90 to 90 and longitude in −180 to 180.

## Tile provider

OpenFreeMap’s Liberty style is the default basemap. MapLibre renders its vector tiles inside Leaflet, which continues to handle pins and marker interactions. The [OpenFreeMap public instance](https://openfreemap.org/quick_start/) requires no API key. Browsers without WebGL 2 or where the vector map fails use OpenStreetMap raster tiles. Both layers show provider attribution.

To explicitly select a raster provider, set `VITE_MAP_TILE_URL` and `VITE_MAP_TILE_ATTRIBUTION` together, then rebuild. Leave the URL unset to use OpenFreeMap. If a network or content security policy restricts map traffic, allow requests to `tiles.openfreemap.org` and any asset origins used by the style. The fallback uses `tile.openstreetmap.org` under the [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/).

Run `npm run lint`, `npm run typecheck`, and `npm run build` in `frontend/`, and `python manage.py test` in `backend/`. To verify a deployment, compare public markers against stored coordinates, apply filters, check the directions URL, and try saving and reloading a location with an authorized manager. A second manager must be unable to edit the same listing.
