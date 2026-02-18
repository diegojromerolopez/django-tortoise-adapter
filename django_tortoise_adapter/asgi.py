"""
ASGI wrapper for Django-Tortoise Adapter.
"""

from typing import Any

from django.conf import settings
from tortoise import Tortoise

from django_tortoise_adapter.core import patch_model


class TortoiseASGIWrapper:
    """
    An ASGI application wrapper that manages Tortoise ORM's lifespan.
    It intercepts lifespan events (startup/shutdown) to initialize and
    close Tortoise connections, translating Django models automatically.
    """

    def __init__(self, application: Any) -> None:
        self.application = application

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    from django.apps import apps

                    # 1. Translate models
                    for app_config in apps.get_app_configs():
                        for model in app_config.get_models():
                            patch_model(model)

                    # 2. Init Tortoise
                    # Default to in-memory sqlite if not configured
                    db_url = "sqlite://:memory:"
                    if (
                        hasattr(settings, "TORTOISE_ORM")
                        and "connections" in settings.TORTOISE_ORM
                    ):
                        db_url = settings.TORTOISE_ORM["connections"].get(
                            "default", db_url
                        )

                    await Tortoise.init(
                        db_url=db_url,
                        modules={"models": ["django_tortoise_adapter.models"]},
                        _enable_global_fallback=True,
                    )
                    await send({"type": "lifespan.startup.complete"})

                elif message["type"] == "lifespan.shutdown":
                    await Tortoise.close_connections()
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        else:
            await self.application(scope, receive, send)


def get_asgi_application() -> TortoiseASGIWrapper:
    """
    Returns a Django ASGI application wrapped with Tortoise ORM lifespan management.
    """
    from django.core.asgi import get_asgi_application as django_get_asgi_application

    return TortoiseASGIWrapper(django_get_asgi_application())
