from typing import Any

from django.apps import apps as django_apps
from django.db import models as django_models
from tortoise import Tortoise

from django_tortoise_adapter.bridge import run_async
from django_tortoise_adapter.translator import TortoiseTranslator


class TortoiseQuerySet:
    """
    A proxy QuerySet that delegates to Tortoise.
    """

    def __init__(self, tortoise_model: type[Any]) -> None:
        self.tortoise_model = tortoise_model
        self._filter_kwargs: dict[str, Any] = {}
        self._order_args: list[str] = []

    def filter(self, **kwargs: Any) -> "TortoiseQuerySet":
        self._filter_kwargs.update(kwargs)
        return self

    def order_by(self, *args: str) -> "TortoiseQuerySet":
        self._order_args.extend(args)
        return self

    def all(self) -> "TortoiseQuerySet":
        return self

    async def count(self) -> int:
        return await self.tortoise_model.filter(  # type: ignore[no-any-return]
            **self._filter_kwargs
        ).count()

    async def first(self) -> Any | None:
        return await self.tortoise_model.filter(**self._filter_kwargs).first()

    async def get(self, **kwargs: Any) -> Any:
        self._filter_kwargs.update(kwargs)
        return await self.tortoise_model.get(**self._filter_kwargs)

    def __await__(self) -> Any:
        qs = self.tortoise_model.filter(**self._filter_kwargs)
        if self._order_args:
            qs = qs.order_by(*self._order_args)
        return qs.all().__await__()  # type: ignore[no-any-return]

    def __aiter__(self) -> Any:
        async def iterator() -> Any:
            qs = self.tortoise_model.filter(**self._filter_kwargs)
            if self._order_args:
                qs = qs.order_by(*self._order_args)
            results = await qs.all()
            for res in results:
                yield res

        return iterator()

    def __iter__(self) -> Any:
        # bridge for legacy sync support
        async def fetch() -> list[Any]:
            return await self.tortoise_model.filter(  # type: ignore[no-any-return]
                **self._filter_kwargs
            ).all()

        results = run_async(fetch())
        return iter(results)


class TortoiseManager(django_models.Manager):
    """
    A Manager that proxies calls to Tortoise.
    """

    def __init__(self, tortoise_model: type[Any]) -> None:
        super().__init__()
        self.tortoise_model = tortoise_model

    def get_queryset(self) -> TortoiseQuerySet:  # type: ignore[override]
        return TortoiseQuerySet(self.tortoise_model)

    async def create(self, **kwargs: Any) -> Any:  # type: ignore[override]
        return await self.tortoise_model.create(**kwargs)

    def all(self) -> TortoiseQuerySet:  # type: ignore[override]
        return self.get_queryset().all()

    def filter(  # type: ignore[override]
        self, *args: Any, **kwargs: Any
    ) -> TortoiseQuerySet:
        return self.get_queryset().filter(*args, **kwargs)

    async def count(self) -> int:  # type: ignore[override]
        return await self.get_queryset().count()

    async def get(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        return await self.get_queryset().get(*args, **kwargs)

    async def first(self) -> Any | None:  # type: ignore[override]
        return await self.get_queryset().first()


async def activate_async(
    _modules: list[str],
    db_url: str = "sqlite://:memory:",
    generate_schemas: bool = True,
) -> None:
    """
    Activates Tortoise backend (Async).

    :param _modules: Unused parameter, kept for compatibility.
    :param db_url: Database URL for Tortoise.
    :param generate_schemas: Whether to generate schemas.
    """
    # 1. Translate models first so they exist in django_tortoise_adapter.models

    # We need to translate BEFORE initializing Tortoise because Tortoise
    # looks for classes in the module
    for app_config in django_apps.get_app_configs():
        for model in app_config.get_models():
            patch_model(model)

    # 2. Init Tortoise pointing to our registry
    await Tortoise.init(
        db_url=db_url, modules={"models": ["django_tortoise_adapter.models"]}
    )

    # 3. Generate schema
    if generate_schemas:
        await Tortoise.generate_schemas(safe=True)


def activate(
    _modules: list[str],
    db_url: str = "sqlite://:memory:",
    generate_schemas: bool = True,
) -> None:
    """
    Activates Tortoise backend (Sync wrapper).
    """
    run_async(
        activate_async(_modules, db_url=db_url, generate_schemas=generate_schemas)
    )


def patch_model(django_model: type[django_models.Model]) -> None:
    # Translate
    try:
        tortoise_cls = TortoiseTranslator.translate_model(django_model)
    except Exception:  # pylint: disable=broad-exception-caught
        # print(f"Skipping {django_model.__name__}: {e}")
        return

    # Patch Manager
    manager = TortoiseManager(tortoise_cls)
    # pylint: disable=attribute-defined-outside-init
    manager.model = django_model

    # Patching 'objects' is the standard way users access the manager
    setattr(django_model, "objects", manager)
