import pytest_asyncio

from app.models.notification import Notification


@pytest_asyncio.fixture
async def notification(db_session, notification_template, group):
    obj = Notification(
        template_id=notification_template.id,
        group_id=group.id,
    )
    db_session.add(obj)
    await db_session.flush()
    return obj
