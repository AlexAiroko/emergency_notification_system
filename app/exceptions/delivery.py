from app.exceptions.base import NotFoundError, ValidationError


class DeliveryNotFoundError(NotFoundError):
    code = "delivery_not_found"
    
    def __init__(self, delivery_id: int) -> None:
        super().__init__(f"Delivery {delivery_id} not found")


class TooManyDeliveriesError(ValidationError):
    code = "too_many_deliveries"
    def __init__(self, count: int, max_count: int) -> None:
        super().__init__(
            f"Too many deliveries: {count} exceeds limit of {max_count}"
        )
