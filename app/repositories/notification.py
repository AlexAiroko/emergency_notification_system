from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.notification import Notification, NotificationStatus
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    model = Notification
    
    async def get_with_relations(self, notification_id: int) -> Notification | None:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.template),
                selectinload(self.model.group),
            )
            .where(self.model.id == notification_id)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
    
    async def update_status(self, notification_id: int, status: NotificationStatus) -> None:
        await self.update(
            notification_id,
            status=status,
        )
    
    async def mark_started(self, notification_id: int) -> None:
        await self.update_status(notification_id, NotificationStatus.IN_PROGRESS)
    
    async def mark_finished(self, notification_id: int) -> None:
        await self.update_status(notification_id, NotificationStatus.SUCCESS)
