from app.exceptions.base import NotFoundError, ValidationError


class UnsupportedImportFileError(ValidationError):
    def __init__(self, filename: str):
        super().__init__(
            f"Unsupported import file '{filename}'. Only .csv and .xlsx files are supported."
        )


class EmptyImportFileError(ValidationError):
    def __init__(self):
        super().__init__("Import file is empty")


class InvalidImportHeaderError(ValidationError):
    def __init__(self, expected: list[str]):
        headers = ", ".join(expected)
        super().__init__(
            f"Invalid file header. Expected columns: {headers}"
        )


class AbsentNameFieldError(ValidationError):
    def __init__(self):
        super().__init__("Name is required")


class ImportJobNotFoundError(NotFoundError):
    def __init__(self, job_id: int):
        super().__init__(f"Import job {job_id} not found")


class FileTooLargeError(ValidationError):
    def __init__(self):
        super().__init__("File is too large")
