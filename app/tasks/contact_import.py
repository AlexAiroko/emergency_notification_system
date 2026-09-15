import asyncio
import logging

from app.celery_app import celery_app
from app.core.async_utils import run_async
from app.core.config import settings
from app.core.s3 import get_s3_client
from app.core.utils import sanitize_filename
from app.db.uow import UnitOfWork
from app.exceptions.contact_import import AbsentNameFieldError
from app.models.contact_method import ChannelType
from app.services.contact import ContactService
from app.services.contact_import.parser_factory import ParserFactory
from app.services.contact_method import ContactMethodService


logger = logging.getLogger(__name__)


async def _download_with_retry(s3, object_name: str) -> bytes:
    last_exc = None
    for attempt in range(1, settings.S3_RETRY_COUNT + 1):
        try:
            return s3.download(object_name)
        except (ConnectionError, TimeoutError, OSError) as exc:
            last_exc = exc
            logger.warning(
                "S3 download attempt %s/%s failed: %s",
                attempt, settings.S3_RETRY_COUNT, exc,
            )
            if attempt < settings.S3_RETRY_COUNT:
                await asyncio.sleep(settings.S3_RETRY_DELAY_SECONDS)
    raise last_exc


async def _process_import(job_id: int):
    s3 = get_s3_client()
    contact_service = ContactService()
    contact_method_service = ContactMethodService()

    async with UnitOfWork() as uow:
        job = await uow.import_job_repo.get(job_id)

        if job is None:
            logger.error("ImportJob %s not found", job_id)
            return

        object_name = f"{settings.IMPORT_DIR}/{job_id}/{sanitize_filename(job.filename)}"

        try:
            file_bytes = await _download_with_retry(s3, object_name)

            parser = ParserFactory.get(job.filename)

            imported = 0
            skipped = 0
            errors = []
            idx = 0

            async for row in parser.parse(job.filename, file_bytes):
                idx += 1
                try:
                    if not row.get("name"):
                        raise AbsentNameFieldError()

                    contact = await contact_service.create_contact(
                        uow=uow,
                        external_id=row.get("external_id"),
                        name=row["name"],
                        is_active=True,
                    )

                    for channel, field in (
                        (ChannelType.EMAIL, "email"),
                        (ChannelType.TELEGRAM, "telegram"),
                        (ChannelType.SMS, "phone"),
                    ):
                        address = row.get(field)
                        if address and str(address).strip():
                            await contact_method_service.create_method(
                                uow=uow,
                                contact_id=contact.id,
                                channel=channel,
                                address=str(address).strip(),
                            )

                    imported += 1

                    if imported % settings.IMPORT_BATCH_SIZE == 0:
                        await uow.commit()
                        await uow.import_job_repo.update_progress(
                            job_id, imported, skipped, errors,
                        )
                        await uow.commit()
                        logger.info(
                            "Import %s: progress %s rows processed",
                            job_id, idx,
                        )

                except Exception as exc:
                    skipped += 1
                    errors.append({
                        "row": idx,
                        "reason": str(exc),
                        "values": row,
                    })
                    logger.warning("Row %s failed: %s", idx, exc)

            job.total = idx
            await uow.import_job_repo.update_progress(
                job_id, imported, skipped, errors,
            )
            await uow.import_job_repo.mark_completed(job_id)
            await uow.commit()

            logger.info(
                "Import %s completed: total=%s imported=%s skipped=%s",
                job_id, idx, imported, skipped,
            )

        except Exception as exc:
            logger.exception("Import %s failed", job_id)
            await uow.import_job_repo.mark_failed(
                job_id, [{"row": 0, "reason": str(exc)}],
            )
            await uow.commit()

        finally:
            try:
                s3.delete(object_name)
            except Exception:
                logger.warning("Failed to cleanup S3: %s", object_name)


@celery_app.task
def import_contacts_task(job_id: int):
    run_async(_process_import(job_id))
