from datetime import datetime, timezone


def utc_now() -> datetime:
    """Returns current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def chunk(items: list[int], size: int) -> list[list[int]]:
    return [items[i:i + size] for i in range(0, len(items), size)]
