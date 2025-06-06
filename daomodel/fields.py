from datetime import datetime, timezone
from typing import TypeVar, Generic
from sqlmodel import Field
from sqlalchemy import JSON


T = TypeVar('T')


class Identifier(Generic[T]):
    """A type annotation for primary key fields.

    Usage:
        class MyModel(DAOModel, table=True)
            id: Identifier[str]
            ...
    """
    pass


class Unsearchable(Generic[T]):
    """A type annotation to mark a field as not searchable.

    Usage:
        class MyModel(DAOModel, table=True)
            ...
            internal_notes: Unsearchable[str]
            ...
    """
    pass


class JSONField(Generic[T]):
    """A type annotation for JSON fields.

    Usage:
        class MyModel(DAOModel, table=True)
            ...
            data: JSONField[dict]
            ...
    """
    pass


class Protected(Generic[T]):
    """A type annotation for foreign key fields with RESTRICT delete behavior.

    This prevents the referenced object from being deleted if it is still referenced.

    Usage:
        class MyModel(DAOModel, table=True)
            ...
            parent: Protected[ParentModel]
            ...
    """
    pass


def utc_now():
    """Returns the current UTC time with timezone information."""
    return datetime.now(timezone.utc)


CurrentTimestampField = Field(default_factory=utc_now)
AutoUpdatingTimestampField = Field(default_factory=utc_now, sa_column_kwargs={'onupdate': utc_now})
