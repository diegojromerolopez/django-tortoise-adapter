import os
import sys

# Ensure the package root is in sys.path
sys.path.insert(0, "/app/adapter_source")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "polls_project.settings")

from django_tortoise_adapter.asgi import get_asgi_application  # noqa: E402

application = get_asgi_application()
