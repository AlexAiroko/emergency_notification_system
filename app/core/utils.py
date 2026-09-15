from datetime import datetime, timezone
import re

def utc_now() -> datetime:
    """Returns current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def chunk(items: list[int], size: int) -> list[list[int]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w.\-]", "_", name)
    name = name.strip("._")
    if len(name.encode("utf-8")) > 1024:
        name = name[:200]
    return name or "unnamed"
