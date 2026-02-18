from typing import Any

from django.db import models as django_models
from tortoise import fields as tortoise_fields
from tortoise import models as tortoise_models


class TortoiseTranslator:  # pylint: disable=too-few-public-methods
    """
    Translates Django models to Tortoise models.
    """

    FIELD_MAPPING = {
        django_models.CharField: tortoise_fields.CharField,
        django_models.IntegerField: tortoise_fields.IntField,
        django_models.BooleanField: tortoise_fields.BooleanField,
        django_models.TextField: tortoise_fields.TextField,
        django_models.FloatField: tortoise_fields.FloatField,
        django_models.DecimalField: tortoise_fields.DecimalField,
        django_models.DateTimeField: tortoise_fields.DatetimeField,
        django_models.DateField: tortoise_fields.DateField,
        django_models.AutoField: tortoise_fields.IntField,  # ID
    }

    @classmethod
    def translate_field(
        cls, django_field: django_models.Field
    ) -> tortoise_fields.Field[Any] | None:
        """
        Translates a single Django field to a Tortoise field.
        """
        # pylint: disable=too-many-branches
        # Iterate over MRO to find the best match
        tortoise_type = None
        for base in type(django_field).mro():
            if base in cls.FIELD_MAPPING:
                tortoise_type = cls.FIELD_MAPPING[base]
                break

        if not tortoise_type:
            # Fallback for now: text field? Or raise?
            # raise NotImplementedError(
            #     f"Field type {type(django_field)} not supported yet."
            # )
            return None

        kwargs: dict[str, Any] = {}

        # Map common attributes
        if django_field.null:
            kwargs["null"] = True

        if django_field.default != django_models.NOT_PROVIDED:
            # Tortoise defaults need to be handled carefully.
            # Django defaults can be callables.
            # Tortoise supports callables as defaults.
            kwargs["default"] = django_field.default

        if isinstance(
            django_field, (django_models.DateField, django_models.DateTimeField)
        ):
            if getattr(django_field, "auto_now", False):
                kwargs["auto_now"] = True
            if getattr(django_field, "auto_now_add", False):
                kwargs["auto_now_add"] = True

        if isinstance(django_field, django_models.CharField):
            kwargs["max_length"] = django_field.max_length

        if isinstance(django_field, django_models.DecimalField):
            kwargs["max_digits"] = django_field.max_digits
            kwargs["decimal_places"] = django_field.decimal_places

        if isinstance(django_field, django_models.AutoField):
            kwargs["primary_key"] = True

        return tortoise_type(**kwargs)  # type: ignore[no-any-return]

    @classmethod
    def translate_model(
        cls, django_model: type[django_models.Model]
    ) -> type[tortoise_models.Model]:
        """
        Translates a Django Model class to a Tortoise Model class.
        """
        meta = django_model._meta  # pylint: disable=protected-access
        attrs: dict[str, Any] = {
            "__module__": django_model.__module__,
        }

        # Internal class Meta for Tortoise
        class Meta:
            table = meta.db_table

        attrs["Meta"] = Meta

        for field in meta.fields:
            if field.is_relation:
                if isinstance(field, django_models.ForeignKey):
                    # We need to link to the related model.
                    # Since all our dynamic models are
                    # in 'django_tortoise_adapter.models',
                    # we can use a string reference "models.ModelName".
                    related_model = field.related_model
                    if isinstance(related_model, str):
                        # Should have been resolved by Django usually, but if not:
                        # "app.Model" -> "models.Model" logic might be needed.
                        # For now assume resolved or accessible via name.
                        relation_name = related_model.split(".")[-1]
                    else:
                        relation_name = str(related_model._meta.object_name)

                    related_name = getattr(field.remote_field, "related_name", None)
                    if related_name is None:
                        related_name = f"{django_model.__name__.lower()}_set"

                    t_field = tortoise_fields.ForeignKeyField(
                        f"models.{relation_name}",
                        related_name=related_name,
                        null=field.null,
                    )  # type: ignore[call-overload]
                    attrs[field.name] = t_field
                continue

            # primary_key in Django -> primary_key in Tortoise (pk is deprecated)
            t_field = cls.translate_field(field)
            if t_field:
                attrs[field.name] = t_field
                if field.primary_key:
                    t_field.primary_key = True  # type: ignore[attr-defined]

        # Handle ManyToManyFields (separate list in Django meta)
        for field in meta.many_to_many:
            if isinstance(field, django_models.ManyToManyField):
                related_model = field.related_model
                if isinstance(related_model, str):
                    relation_name = related_model.split(".")[-1]
                else:
                    relation_name = str(related_model._meta.object_name)

                related_name = getattr(field.remote_field, "related_name", None)
                if related_name is None:
                    related_name = f"{django_model.__name__.lower()}_set"

                t_field = tortoise_fields.ManyToManyField(
                    f"models.{relation_name}",
                    related_name=related_name,
                    through=None,  # Not supporting custom through yet
                )
                attrs[field.name] = t_field

        # Create the Tortoise model class
        tortoise_cls = type(django_model.__name__, (tortoise_models.Model,), attrs)

        # Inject into our internal registry module so Tortoise can find it
        # pylint: disable=import-outside-toplevel
        import django_tortoise_adapter.models

        setattr(django_tortoise_adapter.models, django_model.__name__, tortoise_cls)
        # Update __module__ to point there
        tortoise_cls.__module__ = "django_tortoise_adapter.models"

        return tortoise_cls
