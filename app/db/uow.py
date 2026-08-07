from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories_registry import REPOSITORIES
from app.db.session import session_maker
from app.repositories.base import BaseRepository
from app.repositories.contact import ContactRepository
from app.repositories.contact_method import ContactMethodRepository
from app.repositories.delivery import DeliveryRepository
from app.repositories.group import GroupRepository
from app.repositories.notification import NotificationRepository
from app.repositories.notification_template import NotificationTemplateRepository


class UnitOfWork:
    template_repo: NotificationTemplateRepository
    notification_repo: NotificationRepository
    delivery_repo: DeliveryRepository
    group_repo: GroupRepository
    contact_repo: ContactRepository
    contact_method_repo: ContactMethodRepository
    
    def __init__(self):
        self.session: AsyncSession | None = None

    async def __aenter__(self):
        self.session = session_maker()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            if self.session is not None:
                await self.session.close()

        return False
    
    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not initialized")

        await self.session.commit()

    async def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not initialized")
        
        await self.session.rollback()

    def _get_repository(self, name: str) -> BaseRepository:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not initialized")
        
        repo_class = REPOSITORIES.get(name)

        if not repo_class:
            raise AttributeError(f"No repository: {name}")

        repo = repo_class(self.session)

        setattr(self, name, repo)

        return repo
    
    def __getattr__(self, name: str):
        return self._get_repository(name)
