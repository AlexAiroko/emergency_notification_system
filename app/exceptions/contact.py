from app.exceptions.base import ConflictError, NotFoundError


class ContactNotFoundError(NotFoundError):
    code = "contact_not_found"
    
    def __init__(self, contact_id: int):
        super().__init__(f"Contact {contact_id} not found")


class ContactAlreadyExistsError(ConflictError):
    code = "contact_already_exists"
    
    def __init__(self):
        super().__init__("Contact already exists")
