import unittest

import django
from django.conf import settings

# Configure Django settings before defining models
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django_tortoise_adapter"],
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        SECRET_KEY="test-key",
    )
    django.setup()

from unittest.mock import patch

from django.db import models as django_models
from tortoise import Tortoise

from django_tortoise_adapter.core import activate, patch_model


class TestCore(unittest.IsolatedAsyncioTestCase):
    Simple: type[django_models.Model]

    async def asyncSetUp(self) -> None:
        class Simple(django_models.Model):
            text: django_models.CharField = django_models.CharField(max_length=100)

            class Meta:
                app_label = "unit_tests"

        self.Simple = Simple
        patch_model(Simple)

        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["django_tortoise_adapter.models"]},
        )
        await Tortoise.generate_schemas()

    async def asyncTearDown(self) -> None:
        await Tortoise.close_connections()

    async def test_patch_model(self) -> None:
        # Verify objects is a CoroutineProxy or similar and has expected methods
        self.assertTrue(hasattr(self.Simple.objects, "create"))
        self.assertTrue(hasattr(self.Simple.objects, "get"))

    async def test_create_and_get(self) -> None:
        obj = await self.Simple.objects.create(text="Hello")  # type: ignore[misc]
        self.assertEqual(obj.text, "Hello")

        fetched = await self.Simple.objects.get(text="Hello")  # type: ignore[misc]
        self.assertEqual(fetched.text, "Hello")

    async def test_filter_count(self) -> None:
        await self.Simple.objects.create(text="A")  # type: ignore[misc]
        await self.Simple.objects.create(text="B")  # type: ignore[misc]

        count = await self.Simple.objects.filter(text="A").count()  # type: ignore[misc]
        self.assertEqual(count, 1)

        total = await self.Simple.objects.all().count()  # type: ignore[misc]
        self.assertEqual(total, 2)

    async def test_aiter(self) -> None:
        await self.Simple.objects.create(text="Iter")  # type: ignore[misc]
        texts: list[str] = []
        async for obj in self.Simple.objects.all():
            texts.append(getattr(obj, "text"))
        self.assertIn("Iter", texts)

    def test_activate(self) -> None:
        # Mocking Tortoise.init to avoid side effects during activate call
        with patch("django_tortoise_adapter.core.Tortoise.init") as mock_init:
            with patch(
                "django_tortoise_adapter.core.Tortoise.generate_schemas"
            ) as mock_gen:
                from typing import Any

                # We need to return an awaitable
                async def async_none(*args: Any, **kwargs: Any) -> None:
                    return None

                mock_init.side_effect = async_none
                mock_gen.side_effect = async_none

                activate([])
                self.assertTrue(mock_init.called)
