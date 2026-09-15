import logging

from fastapi import UploadFile

from app.core.config import settings
from app.core.s3 import get_s3_client
from app.core.utils import sanitize_filename
from app.db.uow import UnitOfWork
from app.exceptions.contact_import import (
    FileTooLargeError,
    ImportJobNotFoundError,
    UnsupportedImportFileError,
)
from app.models.import_job import ImportJob
from app.tasks.contact_import import import_contacts_task


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"csv", "xlsx"}


class ContactImportService:
    async def start_import(
        self,
        uow: UnitOfWork,
        file: UploadFile,
    ) -> ImportJob:
        if not file.filename:
            raise UnsupportedImportFileError("<unknown>")

        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedImportFileError(file.filename)

        content = await file.read()

        if len(content) > settings.MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError()

        job = await uow.import_job_repo.create(filename=file.filename)
        await uow.commit()

        s3 = get_s3_client()
        object_name = f"{settings.IMPORT_DIR}/{job.id}/{sanitize_filename(file.filename)}"
        s3.upload(object_name, content)

        import_contacts_task.delay(job.id)

        logger.info(
            "Import job %s created (file=%s, %s bytes)",
            job.id, file.filename, len(content),
        )
        return job

    async def get_import_status(
        self,
        uow: UnitOfWork,
        job_id: int,
    ) -> ImportJob:
        job = await uow.import_job_repo.get(job_id)
        if job is None:
            raise ImportJobNotFoundError(job_id)
        return job
