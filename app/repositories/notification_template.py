from app.models import NotificationTemplate
from app.repositories.active import ActiveRepository


class NotificationTemplateRepository(ActiveRepository):
    model = NotificationTemplate
