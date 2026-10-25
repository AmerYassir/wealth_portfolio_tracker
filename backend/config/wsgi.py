"""WSGI entrypoint. Present for tooling only — nothing serves this project
under WSGI. See README: the backend runs under ASGI/Uvicorn."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
