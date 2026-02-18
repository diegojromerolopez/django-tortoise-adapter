# Django-Tortoise Adapter

> [!WARNING]
> **EXPERIMENTAL**: This repository is currently in an experimental state and is **NOT ready for production use**. APIs and functionality may change without notice.

[![PyPI](https://img.shields.io/pypi/v/django-tortoise-adapter.svg)](https://pypi.org/project/django-tortoise-adapter/)
[![Python Positions](https://img.shields.io/pypi/pyversions/django-tortoise-adapter.svg)](https://pypi.org/project/django-tortoise-adapter/)
[![Tests](https://github.com/diegojromerolopez/django-tortoise-adapter/actions/workflows/test_unit.yml/badge.svg)](https://github.com/diegojromerolopez/django-tortoise-adapter/actions/workflows/test_unit.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

A seamless translation layer that allows you to use [Tortoise ORM](https://tortoise.github.io/) models within a [Django](https://www.djangoproject.com/) project. Run high-performance async database queries without rewriting your existing Django model definitions.

---

## 🚀 Why Use This?

Django's ORM is robust and mature, but its synchronous nature can be a bottleneck in modern async applications (ASGI). While Django has introduced async support, it often wraps synchronous calls in threads. **Tortoise ORM** is a native async ORM inspired by Django, offering high performance and cleaner async syntax.

**Django-Tortoise Adapter** bridges this gap by:
1.  **Zero-Config Migration**: Automatically inspecting your existing Django models and generating corresponding Tortoise models on the fly.
2.  **Incremental Adoption**: Allowing you to switch views to `async` one by one.
3.  **Dual-Stack Support**: Keep using Django's ORM for Admin and legacy views, while using Tortoise for high-throughput API endpoints.

## 📦 Installation

```bash
pip install django-tortoise-adapter
```

## ⚙️ Configuration

To activate the translation layer, you need to call `activate()` during your project's initialization (typically in `AppConfig.ready()` or `wsgi.py/asgi.py`).

```python
# your_project/apps.py
from django.apps import AppConfig
from django_tortoise_adapter import activate

class CoreConfig(AppConfig):
    name = 'your_project.core'

    def ready(self):
        # Initialize Tortoise with an in-memory DB or your actual DB connection string
        activate([], db_url="sqlite://db.sqlite3")
```

## 📖 Usage Guide

### 1. The Strategy: "Async Replacement"
The library patches your Django models to inject `TortoiseManager` which replaces the default `objects` manager. Standard methods like `create`, `get`, `first`, and `count` are now **Async native**.

```python
# models.py
class Question(models.Model):
    # This definition remains standard Django
    text = models.CharField(max_length=200)
```

### 2. Async Usage (High Performance)
In your async views (`async def`), simply `await` the standard manager methods.

```python
# views.py
async def create_question(request):
    # Standard API, but async!
    q = await Question.objects.create(text="Async is fast!")
    return JsonResponse({"id": q.id})

async def list_questions(request):
    data = []
    # Async iteration
    async for q in Question.objects.all():
        data.append({"text": q.text})
    return JsonResponse({"questions": data})
```

**Available Methods:**
-   `await Model.objects.create(**kwargs)`
-   `await Model.objects.get(**kwargs)`
-   `await Model.objects.first()`
-   `await Model.objects.count()`
-   `Model.objects.filter(...)` (Returns chainable, awaitable QuerySet)

### 3. Sync Usage?
This library is designed for **Async Views**. If you need to use the ORM synchronously (e.g. in Django Admin), you should use the standard Django ORM mechanism (which this library does not disable, but `objects` is now async).

> ⚠️ **Important:** `Question.objects` is now an Async Manager. Calling `Question.objects.get(...)` without `await` will return a coroutine and NOT execute the query. If you need synchronous access, consider keeping a separate manager (e.g. `sync_objects = models.Manager()`) or using `asgiref.sync.async_to_sync` explicitly.

## 🤝 Contributing

We welcome contributions!

1.  **Clone the repo**:
    ```bash
    git clone https://github.com/diegojromerolopez/django-tortoise-adapter.git
    cd django-tortoise-adapter
    ```
2.  **Environment**: ALWAYS use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -e .[dev]
    ```
3.  **Run Unit Tests**:
    ```bash
    export PYTHONPATH=$PYTHONPATH:.
    python -m unittest discover django_tortoise_adapter/tests/unit
    ```
4.  **Run E2E Tests**: (Requires Docker)
    ```bash
    docker compose -f django_tortoise_adapter/tests/e2e/docker-compose.e2e.yml run --rm test_runner
    ```
5.  **Linting**: Ensure all checks pass.
    ```bash
    black .
    isort .
    ruff check .
    flake8 .
    mypy .
    ```

## ⚠️ Limitations

This project is currently experimental.
-   **Relationships**: `ForeignKey` is supported (including `related_name` conventions), but `ManyToManyField` support is currently limited.
-   **Complex Meta**: Advanced Django `Meta` options (like `indexes`, `constraints`) may not fully translate to Tortoise yet.
-   **Migrations**: Use Django's `makemigrations` and `migrate` to manage the DB schema. Tortoise is used only for data access. `Aerich` is not supported because models are generated dynamically.

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).

## 🤖 Credits

This project was created with the help of **Antigravity**.
