from app.repositories import (
    ContactRepository,
    ContactMethodRepository,
    NotificationRepository,
    DeliveryRepository,
    GroupRepository,
    NotificationTemplateRepository,
)


REPOSITORIES = {
    "notification_repo": NotificationRepository,
    "delivery_repo": DeliveryRepository,
    "group_repo": GroupRepository,
    "template_repo": NotificationTemplateRepository,
    "contact_repo": ContactRepository,
    "contact_method_repo": ContactMethodRepository,
}
