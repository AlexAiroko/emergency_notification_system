from sqlalchemy import func, select

from app.models.delivery import Delivery, DeliveryStatus
from app.repositories.base import BaseRepository


class DeliveryRepository(BaseRepository):
    model = Delivery
    
    async def create_bulk(self, deliveries: list[Delivery]) -> None:
        self.session.add_all(deliveries)
        await self.flush()
    
    async def get_by_notification(self, notification_id: int) -> list[Delivery]:
        stmt = (
            select(self.model)
            .where(self.model.notification_id == notification_id)
        )
        res = await self.session.execute(stmt)
        return res.scalars().all()
    
    async def update_status(
        self,
        delivery_id: int,
        status: DeliveryStatus,
    ) -> None:
        await self.update(
            delivery_id,
            status=status,
        )
    
    async def mark_sent(
        self,
        delivery_id: int,
        provider_message_id: str | None = None,
    ) -> None:
        await self.update(
            delivery_id,
            status=DeliveryStatus.SENT,
            provider_message_id=provider_message_id,
        )
    
    async def mark_failed(
        self,
        delivery_id: int,
        error_message: str,
    ) -> None:
        await self.update(
            delivery_id,
            status=DeliveryStatus.FAILED,
            error_message=error_message,
        )

    async def get_stats(self, notification_id: int) -> dict[str, int]:
        stmt = (
            select(
                self.model.status,
                func.count(self.model.id)
            )
            .where(self.model.notification_id == notification_id)
            .group_by(self.model.status)
        )
        res = await self.session.execute(stmt)
        stats = {
            status.value: count
            for status, count in res.all()
        }
        return stats
