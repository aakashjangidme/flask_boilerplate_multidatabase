class APIException(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    def to_dict(self) -> dict:
        """Convert the exception to a dictionary."""
        return {"status": "error", "message": self.message, "data": None}


class ValidationError(Exception):
    """Custom exception raised for validation errors."""

    def __init__(self, message):
        super().__init__(message)
