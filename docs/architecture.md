# Technical architecture

| Layer | Responsibility |
| --- | --- |
| React, TypeScript and Vercel | Responsive SPA. Public discovery, role-based dashboards, map UI and typed API services. |
| Django authentication | Stores password hashes and issues revocable sessions for email and password sign-in. |
| Django REST Framework and Gunicorn | Validates tokens, applies database-backed role and ownership checks, exposes application APIs, and serves compiled backend static assets through WhiteNoise. |
| Supabase PostgreSQL | Stores profiles, hostels, room inventory, favourites, roommate profiles, conversations, messages, reports and offer catalogue data. Django migrations define the application schema and restrict direct Data API access. |
| Supabase Storage | Stores image objects in private buckets. Django checks upload permissions and brokers authorized access. |
| Leaflet and OpenStreetMap | Displays approved listings with saved coordinates. Directions are external Google Maps links. |

For a protected request, React sends the Supabase bearer token to Django. Django verifies the signature, issuer and audience, then uses the matching profile’s role and the resource’s ownership or participant membership. Browser claims and presentation UI flags do not confer privileges.

Django validates room capacity and reports the last availability confirmation. Messaging uses short polling. Presentation mode exposes the planned premium experiences without changing account payment state. Billing and checkout remain a preview. See [API details](api.md), [database relationships](database.md), and [deployment settings](deployment.md).
