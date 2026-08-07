from unittest.mock import AsyncMock, Mock


class FakeUnitOfWork:
    def __init__(self):
        self.template_repo = Mock()
        self.notification_repo = Mock()
        self.delivery_repo = Mock()
        self.group_repo = Mock()
        self.contact_repo = Mock()
        self.contact_method_repo = Mock()

        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

        return False
