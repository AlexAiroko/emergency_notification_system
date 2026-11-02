from prometheus_client import Counter, Gauge, Histogram


notifications_total = Counter(
    "ens_notifications_total",
    "Total notifications finalized, by status",
    ("status",),
)

deliveries_total = Counter(
    "ens_deliveries_total",
    "Total delivery attempts, by channel and status",
    ("channel", "status"),
)

delivery_retries_total = Counter(
    "ens_delivery_retries_total",
    "Total delivery retries scheduled, by channel",
    ("channel",),
)

rate_limit_rejects_total = Counter(
    "ens_rate_limit_rejects_total",
    "Total rate limit rejections, by channel",
    ("channel",),
)

notifications_in_progress = Gauge(
    "ens_notifications_in_progress",
    "Notifications currently being processed",
    multiprocess_mode="max",
)

delivery_duration_seconds = Histogram(
    "ens_delivery_duration_seconds",
    "End-to-end delivery duration in seconds, by channel",
    ("channel",),
    buckets=(0.5, 1, 2, 5, 10, 30, 60, 120, 300, 600, 1800),
)
