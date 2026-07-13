from .base import *  # noqa: F401,F403

DEBUG = False

OFFLINE_MODE = True
BACKUP_STORAGE_PATH = BASE_DIR / "backups"
NOTIFICATION_BACKEND = "local_db"

# Local/offline profile uses SQLite to run without requiring a MySQL service.
DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.sqlite3",
		"NAME": BASE_DIR / "db.sqlite3",
	}
}
