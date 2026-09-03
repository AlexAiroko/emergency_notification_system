from unittest.mock import patch

from app.metrics.collector import Counter, Gauge, MetricsCollector
from app.metrics.registry import get_metrics_collector


class TestCounter:
    def test_inc_single_label(self):
        counter = Counter("test_total", "Test counter", ("status",))

        counter.inc(status="ok")

        assert counter._values[("ok",)] == 1

    def test_inc_multiple_labels(self):
        counter = Counter("test_total", "Test counter", ("channel", "status"))

        counter.inc(channel="email", status="sent")

        assert counter._values[("email", "sent")] == 1

    def test_inc_accumulates(self):
        counter = Counter("test_total", "Test counter", ("status",))

        counter.inc(status="ok")
        counter.inc(status="ok")
        counter.inc(status="ok")

        assert counter._values[("ok",)] == 3

    def test_render(self):
        counter = Counter("ens_test_total", "Test help", ("x",))

        counter.inc(x="a")

        output = counter.render()

        assert "# HELP ens_test_total Test help" in output
        assert "# TYPE ens_test_total counter" in output
        assert 'ens_test_total{x="a"} 1' in output

    def test_render_empty(self):
        counter = Counter("ens_test_total", "Test help", ("x",))

        output = counter.render()

        assert "# HELP ens_test_total Test help" in output
        assert len(output) == 2


class TestGauge:
    def test_set(self):
        gauge = Gauge("ens_test", "Test gauge")

        gauge.set(5)

        assert gauge._value == 5

    def test_inc_default(self):
        gauge = Gauge("ens_test", "Test gauge")

        gauge.inc()

        assert gauge._value == 1

    def test_inc_delta(self):
        gauge = Gauge("ens_test", "Test gauge")

        gauge.inc(3)

        assert gauge._value == 3

    def test_render(self):
        gauge = Gauge("ens_test_gauge", "Test gauge")

        gauge.set(5)

        output = gauge.render()

        assert "# HELP ens_test_gauge Test gauge" in output
        assert "# TYPE ens_test_gauge gauge" in output
        assert "ens_test_gauge 5" in output


class TestMetricsCollector:
    def test_render_all_metrics(self):
        collector = MetricsCollector()

        collector.notifications_total.inc(status="success")
        collector.deliveries_total.inc(channel="email", status="sent")
        collector.delivery_retries_total.inc(channel="email")
        collector.rate_limit_rejects_total.inc(channel="email")
        collector.notifications_in_progress.set(3)

        output = collector.render()

        assert "ens_notifications_total" in output
        assert "ens_deliveries_total" in output
        assert "ens_delivery_retries_total" in output
        assert "ens_rate_limit_rejects_total" in output
        assert "ens_notifications_in_progress" in output

    def test_singleton(self):
        with patch("app.metrics.registry._collector", None):
            collector1 = get_metrics_collector()
            collector2 = get_metrics_collector()

            assert collector1 is collector2
