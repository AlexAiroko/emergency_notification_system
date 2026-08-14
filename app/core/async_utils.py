import asyncio
from collections.abc import Coroutine
from typing import Any

_loop: asyncio.AbstractEventLoop | None = None


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Runs a coroutine on a persistent, per-process event loop."""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop.run_until_complete(coro)
