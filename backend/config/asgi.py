"""ASGI entrypoint. Uvicorn loads this. SSE in Phase 5 requires ASGI."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()
