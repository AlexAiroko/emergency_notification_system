from datetime import datetime, timezone


def utc_now() -> datetime:
    """Returns current UTC time with timezone info."""
    return datetime.now(timezone.utc)
