import os
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def csv_env(name, default):
    return [entry.strip() for entry in os.getenv(name, default).split(",") if entry.strip()]


def flag(name, default="false"):
    return os.getenv(name, default).strip().lower() == "true"


PRODUCTION = os.getenv("DJANGO_ENV", "development").strip().lower() == "production"
DEBUG = not PRODUCTION and flag("DJANGO_DEBUG", "true")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or (get_random_secret_key() if DEBUG else "")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required when DJANGO_DEBUG is false.")

ALLOWED_HOSTS = csv_env("DJANGO_ALLOWED_HOSTS", "" if PRODUCTION else "localhost,127.0.0.1,[::1]")
CORS_ALLOWED_ORIGINS = csv_env(
    "CORS_ALLOWED_ORIGINS", "" if PRODUCTION else "http://localhost:5173,http://127.0.0.1:5173"
)
CSRF_TRUSTED_ORIGINS = csv_env("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if PRODUCTION:
    if not ALLOWED_HOSTS or any("*" in host or host.startswith(".") for host in ALLOWED_HOSTS):
        raise ImproperlyConfigured("Production requires explicit DJANGO_ALLOWED_HOSTS.")
    if not CORS_ALLOWED_ORIGINS:
        raise ImproperlyConfigured("Production requires explicit CORS_ALLOWED_ORIGINS.")
    for origin in (*CORS_ALLOWED_ORIGINS, *CSRF_TRUSTED_ORIGINS):
        parts = urlsplit(origin)
        if (parts.scheme != "https" or not parts.hostname or "*" in origin
                or parts.username or parts.password or parts.path or parts.query or parts.fragment):
            raise ImproperlyConfigured("Production CORS and CSRF origins must be exact HTTPS origins.")

SECURE_SSL_REDIRECT = PRODUCTION
SESSION_COOKIE_SECURE = PRODUCTION
CSRF_COOKIE_SECURE = PRODUCTION
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_HSTS_SECONDS", "31536000" if PRODUCTION else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = flag("DJANGO_HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = flag("DJANGO_HSTS_PRELOAD")
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
if PRODUCTION and flag("DJANGO_TRUST_PROXY_HTTPS"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CORS_URLS_REGEX = r"^/api/"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "apps.accounts",
    "apps.hostels",
    "apps.roommates",
    "apps.messaging",
    "apps.subscriptions",
    "apps.moderation",
    "common",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TIME_ZONE = "Africa/Accra"
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

if os.getenv("POSTGRES_HOST"):
    postgres_options = {"sslmode": os.getenv("POSTGRES_SSLMODE", "verify-full" if PRODUCTION else "require")}
    if PRODUCTION and postgres_options["sslmode"] != "verify-full":
        raise ImproperlyConfigured("Production PostgreSQL requires POSTGRES_SSLMODE=verify-full.")
    if os.getenv("POSTGRES_SSLROOTCERT"):
        postgres_options["sslrootcert"] = os.environ["POSTGRES_SSLROOTCERT"]
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "NAME": os.getenv("POSTGRES_DB", "postgres"),
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "OPTIONS": postgres_options,
        }
    }
elif DEBUG:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.getenv("SQLITE_PATH") or ":memory:"}}
else:
    raise ImproperlyConfigured("POSTGRES_HOST is required when DJANGO_DEBUG is false.")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_HOSTEL_BUCKET = os.getenv("SUPABASE_HOSTEL_BUCKET", "hostel-images")
SUPABASE_AVATAR_BUCKET = os.getenv("SUPABASE_AVATAR_BUCKET", "avatars")
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 1

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.SupabaseAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

AVAILABILITY_STALE_HOURS = int(os.getenv("AVAILABILITY_STALE_HOURS", "48"))

PRESENTATION_MODE = flag("PRESENTATION_MODE")
DEMO_SEED_ENABLED = flag("DEMO_SEED_ENABLED")
