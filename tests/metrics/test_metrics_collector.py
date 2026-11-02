from prometheus_client import REGISTRY, CollectorRegistry, generate_latest

from app.metrics.collector import (
    deliveries_total,
    delivery_duration_seconds,
    delivery_retries_total,
    notifications_in_progress,
    notifications_total,
    rate_limit_rejects_total,
)
from app.metrics.registry import get_registry


def _value(name: str, labels: dict | None = None) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


class TestRegistry:
    def test_default_mode_returns_default_registry(self, monkeypatch):
        monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)

        assert get_registry() is REGISTRY

    def test_multiprocess_mode_returns_collector_registry(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", str(tmp_path))

        registry = get_registry()

        assert isinstance(registry, CollectorRegistry)
        assert registry is not REGISTRY


class TestMetrics:
    def test_notifications_total_increments(self):
        before = _value("ens_notifications_total", {"status": "success"})

        notifications_total.labels(status="success").inc()

        assert _value("ens_notifications_total", {"status": "success"}) == before + 1

    def test_deliveries_total_labels(self):
        before = _value("ens_deliveries_total", {"channel": "email", "status": "sent"})

        deliveries_total.labels(channel="email", status="sent").inc()

        assert (
            _value("ens_deliveries_total", {"channel": "email", "status": "sent"})
            == before + 1
        )

    def test_delivery_retries_total_increments(self):
        before = _value("ens_delivery_retries_total", {"channel": "telegram"})

        delivery_retries_total.labels(channel="telegram").inc()

        assert _value("ens_delivery_retries_total", {"channel": "telegram"}) == before + 1

    def test_rate_limit_rejects_total_increments(self):
        before = _value("ens_rate_limit_rejects_total", {"channel": "email"})

        rate_limit_rejects_total.labels(channel="email").inc()

        assert _value("ens_rate_limit_rejects_total", {"channel": "email"}) == before + 1

    def test_notifications_in_progress_gauge(self):
        before = _value("ens_notifications_in_progress")

        notifications_in_progress.inc()
        notifications_in_progress.dec()

        assert _value("ens_notifications_in_progress") == before

    def test_delivery_duration_observe(self):
        before = _value("ens_delivery_duration_seconds_count", {"channel": "email"})

        delivery_duration_seconds.labels(channel="email").observe(1.5)

        assert (
            _value("ens_delivery_duration_seconds_count", {"channel": "email"})
            == before + 1
        )


def test_render_contains_all_metric_names():
    output = generate_latest(REGISTRY).decode()

    assert "ens_notifications_total" in output
    assert "ens_deliveries_total" in output
    assert "ens_delivery_retries_total" in output
    assert "ens_rate_limit_rejects_total" in output
    assert "ens_notifications_in_progress" in output
    assert "ens_delivery_duration_seconds" in output