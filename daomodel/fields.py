from datetime import datetime, timezone
from typing import TypeVar, Generic, get_args, get_origin
from sqlmodel import Field
from sqlalchemy import JSON


T = TypeVar('T')


class Identifier(Generic[T]):
    """
    A type annotation for primary key fields.

    Usage:
        id: Identifier[str]
    """
    pass


def utc_now():
    """Returns the current UTC time with timezone information."""
    return datetime.now(timezone.utc)


CurrentTimestampField = Field(default_factory=utc_now)
AutoUpdatingTimestampField = Field(default_factory=utc_now, sa_column_kwargs={'onupdate': utc_now})


JSONField = Field(sa_type=JSON)
