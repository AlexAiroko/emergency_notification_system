import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.contact_method import ChannelType


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)

    notification_id: Mapped[int] = mapped_column(
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    contact_method_id: Mapped[int] = mapped_column(
        ForeignKey("contact_methods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    channel: Mapped[ChannelType] = mapped_column(
        Enum(
            ChannelType,
            name="channel_type",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    
    address: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(
            DeliveryStatus,
            name="delivery_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=DeliveryStatus.PENDING,
        server_default="pending",
    )
    
    provider_message_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    sent_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    next_attempt_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    notification = relationship("Notification")
    contact = relationship("Contact")
    contact_method = relationship("ContactMethod")

    __table_args__ = (
        Index("ix_delivery_notification_status", "notification_id", "status"),
        Index("ix_delivery_status_next_attempt", "status", "next_attempt_at"),
    )
