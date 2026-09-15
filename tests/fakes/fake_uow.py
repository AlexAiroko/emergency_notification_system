from unittest.mock import AsyncMock, Mock


def make_patched_fake_uow():
    fake = AsyncMock()
    fake.__aenter__ = AsyncMock(return_value=fake)
    fake.__aexit__ = AsyncMock(return_value=False)
    return fake


def make_mock_provider_registry():
    registry = Mock()
    registry.close_all = AsyncMock()
    return registry


class FakeUnitOfWork:
    def __init__(self):
        self.template_repo = Mock()
        self.notification_repo = Mock()
        self.delivery_repo = Mock()
        self.group_repo = Mock()
        self.contact_repo = Mock()
        self.contact_method_repo = Mock()
        self.import_job_repo = Mock()

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
