# models.py
from datetime import datetime
import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator
from pydantic.generics import GenericModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Pagination(BaseModel):
    page: int
    size: int
    total_items: int
    total_pages: int


class PaginatedResponse(GenericModel, Generic[T]):
    links: Any | None = {}
    pagination: Pagination | None = None
    data: list[T] | None = None


class DatabaseResponseModel(BaseModel):
    data: list[Any] = Field(default_factory=list)
    total: int


class RequestModel(BaseModel):
    """Base class for all request models."""

    request_id: str

    @field_validator("request_id")
    def validate_request_id(cls, request_id):
        if not request_id:
            raise ValueError("request_id cannot be empty")
        return request_id.title()


class ResponseModel(BaseModel):
    """Base class for all response models."""

    message: str | None = None
    data: Any = None
    pagelen: int | None = None

    @field_validator("message")
    def validate_message(cls, message):
        if message is None or message == "":
            raise ValueError("message cannot be None or an empty string")
        if not isinstance(message, str):
            raise ValueError("message should be a string")
        return message.title()  # Optional: transform to title case


class UserRequestModel(RequestModel):
    """Model for user requests extending RequestModel."""

    username: str
    age: int

    @field_validator("username")
    def validate_username(cls, username):
        if not username.isalnum():
            raise ValueError("Username must be alphanumeric")
        if not (3 <= len(username) <= 50):
            raise ValueError("Username length must be between 3 and 50 characters")
        return username

    @field_validator("age")
    def validate_age(cls, age):
        if not (18 <= age <= 100):
            raise ValueError("Age must be between 18 and 100")
        return age


class UserModel(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


class UserResponseModel(PaginatedResponse):
    """Model for user responses extending ResponseModel."""

    data: list[UserModel] = []
