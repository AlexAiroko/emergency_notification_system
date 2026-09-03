from app.metrics.collector import MetricsCollector


_collector: MetricsCollector | None = None

def get_metrics_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
