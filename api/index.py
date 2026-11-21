import os
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
os.environ.setdefault("DJANGO_ENV", "production")

from config.wsgi import application


def app(environ, start_response):
    # The rewrite supplies a path even if the runtime replaces PATH_INFO.
    params = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    target = next((value for key, value in reversed(params) if key == "__ucc_path"), None)
    environ["QUERY_STRING"] = urlencode([(key, value) for key, value in params if key != "__ucc_path"])
    path = environ.get("PATH_INFO", "")
    if path in ("", "/", "/api/index", "/api/index.py") and target is not None:
        environ["PATH_INFO"] = "/api/" + target.rstrip("/") + "/"
    return application(environ, start_response)
