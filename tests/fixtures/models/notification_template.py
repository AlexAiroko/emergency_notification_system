import pytest_asyncio

from app.models import NotificationTemplate


@pytest_asyncio.fixture
async def notification_template(db_session):
    template = NotificationTemplate(
        name="T1",
        subject="Subj",
        body="Body text",
        is_active=True,
    )
    db_session.add(template)
    await db_session.flush()
    return template
