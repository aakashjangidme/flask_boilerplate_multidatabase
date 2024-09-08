# models.py
from datetime import datetime
import logging
from typing import Any, Generic, List, TypeVar, Optional

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class PaginationMeta(BaseModel):
    page: int
    size: int
    total_records: int
    total_pages: int


class LinksMeta(BaseModel):
    self: Optional[str] = None
    next: Optional[str] = None
    prev: Optional[str] = None


class MetaModel(BaseModel):
    pagination: PaginationMeta | None = None
    links: LinksMeta | None = None


class PaginatedResponse(GenericModel, Generic[T]):
    data: List[T] | None = None
    metadata: MetaModel | None = Field(None, serialization_alias="_metadata")


class DatabaseResponseModel(BaseModel):
    data: List[Any] = Field(default_factory=list)
    total: int


class RequestModel(BaseModel):
    """Base class for request models."""

    request_id: str

    @validator("request_id")
    def validate_request_id(cls, request_id):
        if not request_id:
            raise ValueError("request_id cannot be empty")
        return request_id.title()


class ResponseModel(BaseModel):
    """Base class for response models."""

    message: Optional[str] = None
    data: Any = None
    pagelen: Optional[int] = None

    @validator("message")
    def validate_message(cls, message):
        if not message:
            raise ValueError("message cannot be None or an empty string")
        if not isinstance(message, str):
            raise ValueError("message should be a string")
        return message.title()  # Optional: transform to title case


class UserRequestModel(RequestModel):
    """Model for user requests extending RequestModel."""

    username: str
    age: int

    @validator("username")
    def validate_username(cls, username):
        if not username.isalnum():
            raise ValueError("Username must be alphanumeric")
        if not (3 <= len(username) <= 50):
            raise ValueError("Username length must be between 3 and 50 characters")
        return username

    @validator("age")
    def validate_age(cls, age):
        if not (18 <= age <= 100):
            raise ValueError("Age must be between 18 and 100")
        return age


class UserModel(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
