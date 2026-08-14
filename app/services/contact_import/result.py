class ImportResult:
    def __init__(
        self,
        total: int = 0,
        imported: int = 0,
        skipped: int = 0,
        errors: list[dict[str, str | int]] | None = None,
    ):
        self.total = total
        self.imported = imported
        self.skipped = skipped
        self.errors = errors or []
