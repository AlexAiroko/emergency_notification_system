from app.models.import_job import ImportJob, ImportJobStatus
from app.repositories.base import BaseRepository


class ImportJobRepository(BaseRepository):
    model = ImportJob

    async def update_progress(
        self,
        job_id: int,
        imported: int,
        skipped: int,
        errors: list[dict],
    ) -> None:
        job = await self.get(job_id)
        job.imported = imported
        job.skipped = skipped
        job.errors = errors
        job.status = ImportJobStatus.IN_PROGRESS
        await self.flush()

    async def mark_completed(self, job_id: int) -> None:
        job = await self.get(job_id)
        job.status = ImportJobStatus.COMPLETED
        await self.flush()

    async def mark_failed(self, job_id: int, errors: list[dict]) -> None:
        job = await self.get(job_id)
        job.status = ImportJobStatus.FAILED
        job.errors = errors
        await self.flush()
