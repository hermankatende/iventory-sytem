import os
from pathlib import Path

from dotenv import load_dotenv

from config.logging import LOGGING


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = env_bool("DEBUG", "1")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "*")

DJANGO_ENV = os.getenv("DJANGO_ENV", "offline").lower()
OFFLINE_MODE = DJANGO_ENV != "online"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.authentication.apps.AuthenticationConfig",
    "apps.users.apps.UsersConfig",
    "apps.inventory.apps.InventoryConfig",
    "apps.products.apps.ProductsConfig",
    "apps.suppliers.apps.SuppliersConfig",
    "apps.customers.apps.CustomersConfig",
    "apps.purchases.apps.PurchasesConfig",
    "apps.sales.apps.SalesConfig",
    "apps.reports.apps.ReportsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "src.infrastructure.persistence",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "src.shared.utils.session_timeout_middleware.SessionTimeoutMiddleware",
    "src.shared.utils.activity_logging_middleware.ActivityLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "src.shared.utils.request_id.RequestIDMiddleware",
    "src.shared.utils.audit_middleware.AuditMiddleware",
    "src.shared.utils.exception_middleware.GlobalExceptionMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "src.presentation.web.context_processors.site_context",
            ],
        },
    }
]

USE_SQLITE = env_bool("USE_SQLITE", "1")

if DJANGO_ENV == "online":
    USE_SQLITE = False
elif DJANGO_ENV in {"offline", "test"}:
    USE_SQLITE = True

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    mysql_options = {"charset": "utf8mb4"}
    mysql_ssl_ca = os.getenv("MYSQL_SSL_CA", "").strip()
    if mysql_ssl_ca:
        mysql_options["ssl"] = {"ca": mysql_ssl_ca}

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQL_DATABASE", "construction_inventory"),
            "USER": os.getenv("MYSQL_USER", "root"),
            "PASSWORD": os.getenv("MYSQL_PASSWORD", "root"),
            "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "PORT": int(os.getenv("MYSQL_PORT", "3306")),
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": mysql_options,
        }
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles")))

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "src.presentation.api.v1.exceptions.custom_exception_handler",
}

LOGGING = LOGGING

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

SESSION_COOKIE_AGE = int(os.getenv("SESSION_TIMEOUT_SECONDS", "1800"))
SESSION_SAVE_EVERY_REQUEST = True

ACCOUNT_INACTIVITY_DAYS = int(os.getenv("ACCOUNT_INACTIVITY_DAYS", "90"))
ACCOUNT_LOCKOUT_THRESHOLD = int(os.getenv("ACCOUNT_LOCKOUT_THRESHOLD", "5"))
ACCOUNT_LOCKOUT_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_MINUTES", "30"))

BACKUP_STORAGE_PATH = BASE_DIR / "backups"
NOTIFICATION_BACKEND = "local_db" if OFFLINE_MODE else "email_or_queue"

if DJANGO_ENV == "online":
    if SECRET_KEY == "unsafe-dev-key-change-me":
        raise RuntimeError("Set DJANGO_SECRET_KEY before running in online mode.")

    if ALLOWED_HOSTS == ["*"]:
        raise RuntimeError("Set ALLOWED_HOSTS explicitly before running in online mode.")

    CSRF_TRUSTED_ORIGINS = env_list(
        "CSRF_TRUSTED_ORIGINS",
        ",".join(f"https://{host}" for host in ALLOWED_HOSTS if host != "*"),
    )
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", "1")
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", "1")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "1")
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1")
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", "0")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_COOKIE_HTTPONLY = env_bool("CSRF_COOKIE_HTTPONLY", "1")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")

if DJANGO_ENV == "test":
    DEBUG = False
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }
    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
    }
