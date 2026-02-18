from typing import Any, TypeVar

from asgiref.sync import async_to_sync

T = TypeVar("T")


def run_async(awaitable: Any) -> Any:
    """
    Helper to run an async awaitable synchronously using asgiref.
    """

    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import nest_asyncio  # type: ignore[import-not-found, import-untyped]

        nest_asyncio.apply(loop)
        if asyncio.iscoroutine(awaitable):
            return loop.run_until_complete(awaitable)
        # If it's a future or other awaitable
        return loop.run_until_complete(asyncio.ensure_future(awaitable))

    async def wrapper() -> Any:
        return await awaitable

    return async_to_sync(wrapper)()
