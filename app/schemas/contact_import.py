from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.import_job import ImportJobStatus


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: ImportJobStatus
    total: int
    imported: int
    skipped: int
    errors: list[dict]
    created_at: datetime
