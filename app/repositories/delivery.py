from datetime import datetime

from sqlalchemy import func, or_, select, update

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
        return list(res.scalars().all())
    
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

    async def mark_retry(
        self,
        delivery_id: int,
        next_attempt_at: datetime,
        error_message: str,
    ) -> None:
        stmt = (
            update(self.model)
            .values(
                status=DeliveryStatus.PENDING,
                attempts=Delivery.attempts + 1,
                next_attempt_at=next_attempt_at,
                error_message=error_message,
            )
            .where(self.model.id == delivery_id)
        )

        await self.session.execute(stmt)
        await self.flush()

    async def get_ready_for_dispatch(self, notification_id: int) -> list[int]:
        """PENDING deliveries that can be sent now"""
        stmt = (
            select(self.model.id)
            .where(
                self.model.notification_id == notification_id,
                self.model.status == DeliveryStatus.PENDING,
                or_(
                    self.model.next_attempt_at.is_(None),
                    self.model.next_attempt_at <= func.now(),
                ),
            )
            .order_by(self.model.id)
        )

        res = await self.session.execute(stmt)
        return list(res.scalars().all())
