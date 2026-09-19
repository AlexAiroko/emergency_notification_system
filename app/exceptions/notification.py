from app.exceptions.base import ConflictError, NotFoundError


class NotificationNotFoundError(NotFoundError):
    code = "notification_not_found"
    
    def __init__(self, notification_id: int) -> None:
        super().__init__(f"Notification {notification_id} not found")


class NotificationAlreadySentError(ConflictError):
    code = "notification_already_sent"

    def __init__(self, notification_id: int) -> None:
        super().__init__(f"Notification {notification_id} already sent")
