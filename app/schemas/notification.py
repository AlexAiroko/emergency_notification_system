from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationStatus


class NotificationCreate(BaseModel):
    template_id: int
    group_id: int
    variables: dict = {}


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    template_id: int
    group_id: int
    status: NotificationStatus
    variables: dict = {}
