from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.contact_method import ChannelType
from app.models.delivery import DeliveryStatus


class DeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    notification_id: int
    contact_id: int
    contact_method_id: int
    channel: ChannelType
    address: str
    status: DeliveryStatus
    provider_message_id: str | None
    error_message: str | None
    sent_at: datetime | None
