import os

from prometheus_client import REGISTRY, CollectorRegistry
from prometheus_client.multiprocess import MultiProcessCollector


def multiprocess_dir() -> str | None:
    """
    Shared directory for prometheus_client multiprocess mode, if configured.

    Read straight from the environment: prometheus_client itself decides its
    mode from os.environ at import time, so this must stay the single source
    of truth (not Settings, which does not export to os.environ).
    """
    return os.environ.get("PROMETHEUS_MULTIPROC_DIR")


def get_registry() -> CollectorRegistry:
    """
    Returns the Prometheus registry to render from.

    When PROMETHEUS_MULTIPROC_DIR is set (Docker: API + workers share a
    directory) the registry aggregates metrics from every live process via
    MultiProcessCollector. Otherwise the in-process default registry is used
    (local dev, tests).
    """
    if multiprocess_dir():
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        return registry

    return REGISTRY
