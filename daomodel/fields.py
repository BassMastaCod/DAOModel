import sqlalchemy
from datetime import datetime, timezone
from typing import Optional, Type, get_origin
from sqlmodel import Field
from sqlalchemy import Column, Enum, JSON


def PrimaryKey(**kwargs):
    """Creates a primary key Field with appropriate defaults based on type annotations.

    If used with Optional typing, automatically sets default=None.
    """
    if get_origin(kwargs.get('annotation')) is Optional:
        kwargs.setdefault('default', None)
    return Field(primary_key=True, **kwargs)


def PrimaryForeignKey(foreign_property: str | Column, **kwargs) -> Field:
    """Creates a Field that is both a Primary Key and Foreign Key.

    If used with Optional typing, automatically sets default=None.

    :param foreign_property: The table/column reference for the foreign key
    :return: The SQLModel Field object defining the sa_column
    """
    return ForeignKey(foreign_property, primary_key=True, **kwargs)


def ForeignKey(foreign_property: str | Column,
               primary_key: Optional[bool] = False,
               **kwargs) -> Field:
    """Shortcut for creating a Field that is a ForeignKey.

    If used with Optional type, automatically sets ondelete='SET NULL'.
    Otherwise, deletions and updates are set to cascade by default.

    :param foreign_property: The table/column reference for the foreign key
    :param primary_key: True if this field is also a primary key
    :return: The SQLModel Field object defining the sa_column
    """
    if get_origin(kwargs.get('annotation')) is Optional:
        kwargs.setdefault('ondelete', 'SET NULL')

    return Field(
        sa_column=Column(
            sqlalchemy.ForeignKey(
                foreign_property,
                ondelete=kwargs.pop('ondelete', 'CASCADE'),
                onupdate='CASCADE'),
            primary_key=primary_key),
        **kwargs)


def EnumField(enum_class: Type) -> Field:
    """Creates a Field for SQLAlchemy Enum types.

    :param enum_class: The Enum class to use for this field
    :return: A Field configured to use the specified Enum
    """
    return Field(sa_type=Enum(enum_class))


def utc_now():
    """Returns the current UTC time with timezone information."""
    return datetime.now(timezone.utc)


CurrentTimestampField = Field(default_factory=utc_now)
AutoUpdatingTimestampField = Field(default_factory=utc_now, sa_column_kwargs={"onupdate": utc_now})


UniqueField = Field(unique=True)
RequiredField = Field(nullable=False)
IndexedField = Field(index=True)
JSONField = Field(sa_type=JSON)
