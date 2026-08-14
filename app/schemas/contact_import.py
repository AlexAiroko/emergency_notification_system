from pydantic import BaseModel, Field


class ImportErrorItem(BaseModel):
    row: int
    reason: str


class ContactImportResponse(BaseModel):
    message: str
    total: int
    imported: int
    skipped: int
    errors: list[ImportErrorItem] = Field(default_factory=list)
