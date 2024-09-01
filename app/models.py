# models.py
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class BaseRequest:
    """Base class for all request models."""

    request_id: Optional[str] = field(default=None)


@dataclass
class BaseResponse:
    """Base class for all response models."""

    message: str
    data: Any


@dataclass
class UserRequest(BaseRequest): ...


@dataclass
class UserResponse(BaseResponse):
    data: Optional[dict] = field(default_factory=dict)
