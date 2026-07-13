import os
from django.core.wsgi import get_wsgi_application

current = os.getenv("DJANGO_SETTINGS_MODULE", "").strip()
if current in {"", "config.settings.offline", "config.settings.online", "config.settings.test", "config.settings.base"}:
	os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

application = get_wsgi_application()
