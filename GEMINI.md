# Project Aim: Django-Tortoise Translation Layer

## Goal
The goal of this project is to create a translation layer between Django ORM and Tortoise ORM that provides **the same API interface** as Django but backed by Tortoise's asynchronous engine. The user should only need to install the library, configure usage, and **add the `await` keyword** to their ORM calls (e.g., `await Question.objects.create(...)`).

## Key Features
-   **Same API, internal translation**: Exposes standard Django methods (`create`, `get`, `filter`, `all`) but they return awaitables.
-   **Seamless Integration**: Translates Django `models.Model` definitions to Tortoise `Model` definitions dynamically.
-   **Async First**: Designed for Django Async Views.

## Architecture

### Async Replacement
The library replaces the default Django Manager (`objects`) with a `TortoiseManager` where standard methods (`create`, `get`, etc.) are asynchronous (return coroutines) and must be awaited.

### Implementation Strategy
1.  **Dynamic Model Generation**: Inspects Django models at runtime (e.g., in `AppConfig.ready()`) and generates corresponding Tortoise models.
2.  **Manager Patching**: Swaps the default Django Manager (`objects`) with a Proxy Manager that delegates to Tortoise async methods.
3.  **No Code Changes (Models)**: Existing Django model definitions remain untouched. Users only modify their views to be `async` and use `await`.

## Testing & Quality
-   **Test Suite Architecture**:
    -   **Unit Tests**: Located in `django_tortoise_adapter/tests/unit/`. These tests MUST be self-contained and SHOULD NOT depend on external applications or the `tests/e2e/` folder. Define models locally within the test files or in isolated modules.
    -   **End-to-End (E2E) Tests**: Located in `django_tortoise_adapter/tests/e2e/`. These tests use a full Django project (`polls_project`) and are run within Docker containers.
-   **Test Suite**: A strictly typed, linted test suite using `unittest.IsolatedAsyncioTestCase` for async tests.
-   **Coverage**: 100% unit test coverage is required.
-   **Mocking**: All mock calls must be validated.
-   **Example Project**: A Django project within the repository configured to use the library.
-   **Linters**: `black`, `flake8`, `mypy`, `ruff`, `isort`.
-   **Environment**: ALWAYS use a virtual environment (`venv`, `conda`, `uv`, etc.) for development and testing.
-   **Type Hints**: Use Python 3.10+ syntax (e.g., `list[str]` instead of `List[str]`, `str | None` instead of `Optional[str]`).
-   **Imports**: Do NOT use relative imports. Always use absolute imports (e.g., `from django_tortoise_adapter.core import ...` instead of `from .core import ...`).

## Database Migrations & Schema
-   **Strategy**: Use Django's `makemigrations` and `migrate` to manage the DB schema.
-   **Tortoise Actions**: Tortoise is used mainly for data access. `Tortoise.generate_schemas()` is used in tests/dev but should be avoided in production if Django manages the DB.
-   **Compatibility**: Current translator handles basic fields and table names. Relationships (Foreign Keys) and `db_column` overrides need explicit translation logic to match Django's schema exactly.

## E2E Testing Note
When modifying or interacting with `django_tortoise_adapter/tests/e2e/docker-compose.e2e.yml`, the build `context` must be preserved as `.` (the `e2e` directory itself). The parent repository is mounted inside the container actively via volumes (`../../../:/app/adapter_source`).
