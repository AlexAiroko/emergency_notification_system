class Counter:
    def __init__(self, name: str, help_text: str, label_names: tuple[str, ...]):
        self.name = name
        self.help_text = help_text
        self.label_names = label_names
        self._values: dict[tuple[str, ...], int] = {}

    def inc(self, **labels) -> None:
        key = tuple(labels[name] for name in self.label_names)
        self._values[key] = self._values.get(key, 0) + 1

    def render(self) -> list[str]:
        lines = [
            f"# HELP {self.name} {self.help_text}",
            f"# TYPE {self.name} counter",
        ]
        for key, count in sorted(self._values.items()):
            labels = ",".join(f'{n}="{v}"' for n, v in zip(self.label_names, key))
            lines.append(f"{self.name}{{{labels}}} {count}")
        return lines


class Gauge:
    def __init__(self, name: str, help_text: str):
        self.name = name
        self.help_text = help_text
        self._value: int = 0

    def set(self, value: int) -> None:
        self._value = value

    def inc(self, delta: int = 1) -> None:
        self._value += delta

    def render(self) -> list[str]:
        return [
            f"# HELP {self.name} {self.help_text}",
            f"# TYPE {self.name} gauge",
            f"{self.name} {self._value}",
        ]


class MetricsCollector:
    def __init__(self):
        self.notifications_total = Counter(
            "ens_notifications_total",
            "Total notifications processed",
            ("status",),
        )
        self.deliveries_total = Counter(
            "ens_deliveries_total",
            "Total deliveries processed",
            ("channel", "status"),
        )
        self.delivery_retries_total = Counter(
            "ens_delivery_retries_total",
            "Total delivery retries",
            ("channel",),
        )
        self.rate_limit_rejects_total = Counter(
            "ens_rate_limit_rejects_total",
            "Rate limit rejections",
            ("channel",),
        )
        self.notifications_in_progress = Gauge(
            "ens_notifications_in_progress",
            "Notifications currently being processed",
        )

    def render(self) -> str:
        lines = []
        for metric in (
            self.notifications_total,
            self.deliveries_total,
            self.delivery_retries_total,
            self.rate_limit_rejects_total,
            self.notifications_in_progress,
        ):
            lines.extend(metric.render())
        return "\n".join(lines) + "\n"
