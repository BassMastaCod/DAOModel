from datetime import datetime, timezone, date
from typing import TypeVar, Generic, Any, Optional

from pydantic import computed_field
from pydantic.v1.datetime_parse import parse_datetime
from sqlmodel import Field
from sqlalchemy import Column
from sqlalchemy.types import TypeDecorator, DateTime
from sqlmodel.main import FieldInfo

from daomodel.util import reference_of

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


class ReferenceTo(FieldInfo):
    """Shortcut for defining a foreign key field.

    This class is used by the metaclass to set up foreign key constraints.
    It stores the target information, which the metaclass can then use
    to create the appropriate foreign key constraints and configurations.

    :param target: Either a string in the format 'table.column', a Column object, or a model attribute
    :param **kwargs: Additional arguments to pass to Field

    Usage:
        class MyModel(DAOModel, table=True)
            ...
            other_id: int = ReferenceTo('other_model.id')
            # or
            other_id: int = ReferenceTo(OtherModel.id)
    """
    def __init__(self, target: Optional[str|Column|Any] = None, **kwargs: Any):
        if 'foreign_key' not in kwargs:
            kwargs['foreign_key'] = (
                target if isinstance(target, str) else
                reference_of(target) if target is not None else
                None
            )
        super().__init__(**kwargs)


class no_case_str(str):
    """Marker type for a case-insensitive string column."""
    pass


class utc_datetime(datetime):
    """Marker type for a UTC datetime column."""
    pass


class server_datetime(datetime):
    """Marker type for a server datetime column."""
    pass


class UTCDateTime(TypeDecorator):
    """SQLAlchemy TypeDecorator for UTC datetime columns."""
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[datetime]:
        if value is not None:
            if isinstance(value, str):
                value = parse_datetime(value)
            elif isinstance(value, date) and not isinstance(value, datetime):
                value = datetime.combine(value, datetime.min.time())

            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Optional[datetime]:
        if value is not None:
            if isinstance(value, str):
                value = parse_datetime(value)
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value


class ServerDateTime(TypeDecorator):
    """SQLAlchemy TypeDecorator for server local datetime columns."""
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[datetime]:
        if value is not None:
            if isinstance(value, str):
                value = parse_datetime(value)
            elif isinstance(value, date) and not isinstance(value, datetime):
                value = datetime.combine(value, datetime.min.time())

            value = value.astimezone(timezone.utc)
            _to_server_local(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Optional[datetime]:
        if value is not None:
            if isinstance(value, str):
                value = parse_datetime(value)
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return _to_server_local(value)
        return value


class ServerDateTimeError(ValueError):
    """Indicates that a datetime cannot be represented as server-local time on this platform."""
    def __init__(self, value: datetime):
        self.detail = (
            f'Cannot convert {value.isoformat()} to server-local time on this platform '
            f'(Windows cannot represent datetimes whose local time predates 1970-01-01). '
            f'This may be existing data migrated from a non-Windows system, or a value too early to '
            f'be displayed as local time on Windows. To fix it: store the value in UTC instead by '
            f'using `utc_datetime`, or correct the stored value on the system that created it.'
        )


def _to_server_local(value: datetime) -> datetime:
    """Converts a UTC-aware datetime to server-local time, raising a clear error if the platform cannot do so."""
    try:
        return value.astimezone()
    except OSError as err:
        raise ServerDateTimeError(value) from err


def utc_now():
    """Returns the current UTC time with timezone information."""
    return datetime.now(timezone.utc)


CurrentTimestampField = Field(default_factory=utc_now)
AutoUpdatingTimestampField = Field(default_factory=utc_now, sa_column_kwargs={'onupdate': utc_now})
