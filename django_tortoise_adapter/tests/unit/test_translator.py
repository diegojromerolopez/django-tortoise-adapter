import unittest
from typing import Any

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

from django.db import models as django_models
from tortoise import fields as tortoise_fields
from tortoise import models as tortoise_models

from django_tortoise_adapter.translator import TortoiseTranslator


class TestTranslator(unittest.TestCase):
    def test_translate_field_char(self) -> None:
        d_field: django_models.CharField = django_models.CharField(
            max_length=100, null=True, default="test"
        )
        t_field = TortoiseTranslator.translate_field(d_field)
        self.assertIsNotNone(t_field)
        assert t_field is not None
        self.assertIsInstance(t_field, tortoise_fields.CharField)
        self.assertEqual(getattr(t_field, "max_length"), 100)
        self.assertTrue(t_field.null)
        self.assertEqual(t_field.default, "test")

    def test_translate_field_int(self) -> None:
        d_field: django_models.IntegerField = django_models.IntegerField(null=False)
        t_field = TortoiseTranslator.translate_field(d_field)
        self.assertIsNotNone(t_field)
        assert t_field is not None
        self.assertIsInstance(t_field, tortoise_fields.IntField)
        self.assertFalse(t_field.null)

    def test_translate_field_bool(self) -> None:
        d_field: django_models.BooleanField = django_models.BooleanField(default=True)
        t_field = TortoiseTranslator.translate_field(d_field)
        self.assertIsNotNone(t_field)
        assert t_field is not None
        self.assertIsInstance(t_field, tortoise_fields.BooleanField)
        self.assertTrue(t_field.default)

    def test_translate_field_datetime(self) -> None:
        d_field: django_models.DateTimeField = django_models.DateTimeField(
            auto_now_add=True
        )
        t_field = TortoiseTranslator.translate_field(d_field)
        self.assertIsInstance(t_field, tortoise_fields.DatetimeField)
        self.assertTrue(getattr(t_field, "auto_now_add", False))

    def test_translate_model_simple(self) -> None:
        class SimpleModel(django_models.Model):
            name: django_models.CharField = django_models.CharField(max_length=50)
            age: django_models.IntegerField = django_models.IntegerField()

            class Meta:
                app_label = "unit_tests"

        t_model = TortoiseTranslator.translate_model(SimpleModel)
        self.assertTrue(issubclass(t_model, tortoise_models.Model))
        self.assertEqual(t_model.__name__, "SimpleModel")
        self.assertIn("name", t_model._meta.fields_map)
        self.assertIn("age", t_model._meta.fields_map)

    def test_translate_related_name_convention(self) -> None:
        # Verify that related_name follows _set convention for FK
        class Parent(django_models.Model):
            class Meta:
                app_label = "unit_tests"

        class Child(django_models.Model):
            parent: django_models.ForeignKey = django_models.ForeignKey(
                Parent, on_delete=django_models.CASCADE
            )

            class Meta:
                app_label = "unit_tests"

        TortoiseTranslator.translate_model(Parent)
        t_child = TortoiseTranslator.translate_model(Child)

        # In Tortoise, the reverse relation is injected into the target model
        # during Tortoise.init(). Since we're not initializing here, we check
        # the property on the source field.
        t_field: Any = t_child._meta.fields_map["parent"]
        self.assertEqual(t_field.related_name, "child_set")

    def test_translate_m2m_related_name_convention(self) -> None:
        # Verify that related_name follows _set convention for M2M
        class Tag(django_models.Model):
            class Meta:
                app_label = "unit_tests"

        class Post(django_models.Model):
            tags: django_models.ManyToManyField = django_models.ManyToManyField(Tag)

            class Meta:
                app_label = "unit_tests"

        t_tag = TortoiseTranslator.translate_model(Tag)
        self.assertIsNotNone(t_tag)
        t_post = TortoiseTranslator.translate_model(Post)

        t_field: Any = t_post._meta.fields_map["tags"]
        self.assertEqual(t_field.related_name, "post_set")

    def test_translate_explicit_related_name(self) -> None:
        # Verify that explicit related_name is respected
        class Owner(django_models.Model):
            class Meta:
                app_label = "unit_tests"

        class Pet(django_models.Model):
            owner: django_models.ForeignKey = django_models.ForeignKey(
                Owner, on_delete=django_models.CASCADE, related_name="pets"
            )

            class Meta:
                app_label = "unit_tests"

        t_owner = TortoiseTranslator.translate_model(Owner)
        self.assertIsNotNone(t_owner)
        t_pet = TortoiseTranslator.translate_model(Pet)

        t_field: Any = t_pet._meta.fields_map["owner"]
        self.assertEqual(t_field.related_name, "pets")
