from app.exceptions.base import NotFoundError


class ContactMethodNotFoundError(NotFoundError):
    code = "contact_method_not_found"
    
    def __init__(self, method_id: int):
        super().__init__(f"Contact method {method_id} not found")
