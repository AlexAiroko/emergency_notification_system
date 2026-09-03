import logging

from fastapi import UploadFile

from app.db.uow import UnitOfWork
from app.exceptions.contact_import import AbsentNameFieldError
from app.models.contact_method import ChannelType
from app.services.contact import ContactService
from app.services.contact_import.parser_factory import ParserFactory
from app.services.contact_import.result import ImportResult
from app.services.contact_method import ContactMethodService


logger = logging.getLogger(__name__)


class ContactImportService:
    def __init__(self):
        self.contact_service = ContactService()
        self.contact_method_service = ContactMethodService()

    async def import_contacts(
        self,
        uow: UnitOfWork,
        file: UploadFile,
    ) -> ImportResult:
        """
        Imports contacts from CSV/XLSX.

        Returns:
            number of imported contacts.
        """
        
        parser = ParserFactory.get(file.filename)
        rows = await parser.parse(file)
        
        result = ImportResult(total=len(rows))

        logger.info(
            "Starting import of %s contacts from '%s'",
            result.total,
            file.filename,
        )

        for idx, row in enumerate(rows, start=1):
            try:
                imported = await self._import_row(uow, row)

                if imported:
                    result.imported += 1
                else:
                    result.skipped += 1

            except Exception as exc:
                result.skipped += 1
                result.errors.append(
                    {
                        "row": idx,
                        "reason": str(exc),
                    }
                )

                logger.warning(
                    "Row %s import failed: %s",
                    idx,
                    exc,
                )

        logger.info(
            "Import finished: total=%s imported=%s skipped=%s errors=%s",
            result.total,
            result.imported,
            result.skipped,
            len(result.errors),
        )

        return result

    async def _import_row(self, uow: UnitOfWork, row: dict) -> bool:
        """
        Returns:
        - True -> imported
        - False -> skipped
        """

        if not row.get("name"):
            raise AbsentNameFieldError()
        
        contact = await self.contact_service.create_contact(
            uow=uow,
            external_id=row.get("external_id"),
            name=row["name"],
            is_active=True,
        )

        await self._create_methods(uow, contact.id, row)

        return True
    
    async def _create_methods(
            self,
            uow: UnitOfWork,
            contact_id: int,
            row: dict,
    ) -> None:
        for channel, field in (
            (ChannelType.EMAIL, "email"),
            (ChannelType.TELEGRAM, "telegram"),
            (ChannelType.SMS, "phone"),
        ):
            address = row.get(field)

            if not address or not address.strip():
                continue

            await self.contact_method_service.create_method(
                uow=uow,
                contact_id=contact_id,
                channel=channel,
                address=str(address).strip(),
            )
