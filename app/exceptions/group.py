from app.exceptions.base import ConflictError, NotFoundError, ValidationError


class GroupNotFoundError(NotFoundError):
    code = "group_not_found"
    
    def __init__(self, group_id: int):
        super().__init__(f"Group {group_id} not found")


class GroupAlreadyExistsError(ConflictError):
    code = "group_already_exists"
    def __init__(self):
        super().__init__("Group already exists")


class GroupInactiveError(ValidationError):
    code = "group_inactive"
    def __init__(self, group_id: int) -> None:
        super().__init__(f"Group {group_id} is inactive")
