import os
import sys
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
os.environ.setdefault("DJANGO_ENV", "production")

@lru_cache(maxsize=1)
def django_application():
    if os.environ["DJANGO_ENV"].strip().lower() == "production":
        # This repository's public Vercel domain is stable across deployments.
        production_host = "ucc-hostelhub.vercel.app"
        configured_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "").strip()
        os.environ["DJANGO_ALLOWED_HOSTS"] = ",".join(filter(None, (production_host, configured_hosts)))

    from config.wsgi import application

    return application


def app(environ, start_response):
    required = ("DJANGO_SECRET_KEY", "CORS_ALLOWED_ORIGINS", "POSTGRES_HOST")
    if os.environ["DJANGO_ENV"].strip().lower() == "production" and not all(
        os.getenv(name, "").strip() for name in required
    ):
        start_response("503 Service Unavailable", [
            ("Content-Type", "application/json"),
            ("Cache-Control", "no-store"),
        ])
        return [b'{"detail":"The backend is awaiting deployment configuration."}']

    # The rewrite supplies a path even if the runtime replaces PATH_INFO.
    params = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    target = next((value for key, value in reversed(params) if key == "__ucc_path"), None)
    environ["QUERY_STRING"] = urlencode([(key, value) for key, value in params if key != "__ucc_path"])
    path = environ.get("PATH_INFO", "")
    if target is not None and (not path.startswith("/api/") or path.rstrip("/") in ("/api/index", "/api/index.py")):
        environ["PATH_INFO"] = "/api/" + target.rstrip("/") + "/"
    return django_application()(environ, start_response)
