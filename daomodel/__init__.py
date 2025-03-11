from typing import Any, Self, Iterable, Union, Optional

import sqlalchemy
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Engine, MetaData, Connection
from str_case_util import Case
from sqlalchemy.ext.declarative import declared_attr

from daomodel.util import reference_of, names_of, in_order, retain_in_dict, remove_from_dict


property_categories = ['all', 'pk', 'fk', 'standard', 'assigned', 'unset', 'defaults', 'none']


class DAOModel(SQLModel):
    """An SQLModel specifically designed to support a DAO."""

    @declared_attr
    def __tablename__(self) -> str:
        return self.normalized_name()

    @classmethod
    def has_column(cls, column: Column) -> bool:
        """Returns True if the specified Column belongs to this DAOModel"""
        return column.table.name == cls.__tablename__

    @classmethod
    def normalized_name(cls) -> str:
        """
        A normalized version of this Model name.

        :return: The model name in snake_case form
        """
        return Case.SNAKE_CASE.format(cls.__name__)

    @classmethod
    def doc_name(cls) -> str:
        """
        A reader friendly version of this Model name to be used within documentation.

        :return: The model name in Title Case
        """
        return Case.TITLE_CASE.format(cls.__name__)

    @classmethod
    def get_pk(cls) -> list[Column]:
        """
        Returns the Columns that comprise the Primary Key for this Model.

        :return: A list of primary key columns
        """
        return cls.__table__.primary_key

    @classmethod
    def get_pk_names(cls) -> list[str]:
        """
        Returns the names of Columns that comprise the Primary Key for this Model.

        :return: A list of str of the primary key
        """
        return names_of(cls.get_pk())

    def get_pk_values(self) -> tuple[Any, ...]:
        """
        Returns the values that comprise the Primary Key for this instance of the Model.

        :return: A tuple of primary key values
        """
        return tuple(list(getattr(self, key) for key in names_of(self.get_pk())))

    def get_pk_dict(self) -> dict[str, Any]:
        """
        Returns the dictionary Primary Keys for this instance of the Model.

        :return: A dict of primary key names/values
        """
        return self.model_dump(include=set(self.get_pk_names()))

    @classmethod
    def get_fks(cls) -> set[Column]:
        """
        Returns the Columns of other objects that are represented by Foreign Keys for this Model.

        :return: An unordered set of columns
        """
        return {fk.column for fk in cls.__table__.foreign_keys}

    @classmethod
    def get_fk_properties(cls) -> set[Column]:
        """
        Returns the Columns of this Model that represent Foreign Keys.

        :return: An unordered set of foreign key columns
        """
        return {fk.parent for fk in cls.__table__.foreign_keys}

    @classmethod
    def get_references_of(cls, model: type[Self]) -> set[Column]:
        """
        Returns the Columns of this Model that represent Foreign Keys of the specified Model.

        :return: An unordered set of foreign key columns
        """
        return {fk.parent for fk in cls.__table__.foreign_keys if model.has_column(fk.column)}

    @classmethod
    def get_properties(cls) -> Iterable[Column]:
        """
        Returns all the Columns for this Model.

        Column order will match order they are defined in code.
        Inherited properties will be listed first.

        :return: A list of columns
        """
        return cls.__table__.c

    def get_property_names(self, **kwargs: bool) -> list[str]:
        """Returns the names of the specified properties of this Model

        Supported property categories to specify are:
            all: All model properties including those inherited
            pk: Primary Key properties
            fk: Foreign Key properties
            standard: All other properties (that aren't pk or fk)
            assigned: Properties that don't match the following categories (can include pk/fk)
            unset: Properties that have not been explicitly set (see Pydantic.model_dump for more info)
            defaults: Properties that are equivalent to their default value (see Pydantic.model_dump for more info)
            none: Properties that do not have a value (see Pydantic.model_dump for more info)
        Property categories may be set to True (to include) or False (to exclude).
        If no arguments are provided, no properties will be returned.
        The categories are added/removed in the order that they are encountered as arguments.
            Therefore, arguments of get_property_names(pk=False, all=True) will result in all properties.
        unset, defaults, and none will overlap with each other and the other categories
            so order is important to get the properties you intend.

        :param kwargs: The property categories to include or exclude
        :return: A list of property names in the order they are defined within the code (see get_properties)
        """
        property_order = names_of(self.get_properties())
        all_properties = set(property_order)
        result = set()

        for key, value in kwargs.items():
            if key not in property_categories:
                raise ValueError(f'Unexpected keyword argument {key} is not one of {property_categories}')
            if key is 'all':
                props = all_properties
            elif key in 'pk':
                props = self.get_pk_names()
            elif key is 'fk':
                props = names_of(self.get_fk_properties())
            elif key is 'assigned':
                props = self.model_dump(exclude_unset=True, exclude_defaults=True, exclude_none=True)
            else:
                if key is 'standard':
                    exclude = self.get_pk_names() + names_of(self.get_fk_properties())
                else:
                    exclude = self.model_dump(**{f'exclude_{key}': True})
                props = all_properties.difference(exclude)

            result = result.union(props) if value else result.difference(props)
        return in_order(result, property_order)

    def get_property_values(self, **kwargs: bool) -> dict[str, Any]:
        """Reads values of the specified properties of this Model.

        :param kwargs: see get_property_names()
        :return: a dict of property names and their values
        """
        return self.get_values_of(self.get_property_names(**kwargs))

    def get_value_of(self, column: Column|str) -> Any:
        """Shortcut function to return the value for the specified Column"""
        if not isinstance(column, str):
            column = column.name
        return getattr(self, column)

    def get_values_of(self, columns = Iterable[Column|str]) -> dict[str, Any]:
        """Reads the values of multiple columns.

        :param columns: The Columns, or their names, to read
        :return: A dict of the column names and their values
        """
        return {column: self.get_value_of(column) for column in columns}

    def compare(self, other, include_pk: Optional[bool] = False) -> dict[str, tuple[Any, Any]]:
        """Compares this model to another, producing a diff.

        By default, primary keys are excluded in the diff.
        While designed to compare like models, it should work between different model types. Though that is untested.

        :param other: The model to compare to this one
        :param include_pk: True if you want to include the primary key in the diff
        :return: A dictionary of property names with a tuple of this instances value and the other value respectively
        """
        args = {'all': True}
        if not include_pk:
            args['pk'] = False
        source_values = self.get_property_values(**args)
        other_values = other.get_property_values(**args)
        diff = {}
        for k, v in source_values.items():
            if other_values[k] != v:
                diff[k] = (v, other_values[k])
        return diff

    @classmethod
    def get_searchable_properties(cls) -> Iterable[Column|tuple[type[Self], ..., Column]]:
        """
        Returns all the Columns for this Model that may be searched using the DAO find function.

        :return: A list of searchable columns
        """
        return cls.get_properties()

    @classmethod
    def find_searchable_column(cls, prop: Union[str, Column], foreign_tables: list[type[Self]]) -> Column:
        """
        Returns the specified searchable Column.

        :param prop: str type reference of the Column or the Column itself
        :param foreign_tables: A list of foreign tables to populated with tables of properties deemed to be foreign
        :return: The searchable Column
        :raises: Unsearchable if the property is not Searchable for this class
        """
        if type(prop) is not str:
            prop = reference_of(prop)
        for column in cls.get_searchable_properties():
            tables = []
            if type(column) is tuple:
                tables = column[:-1]
                column = column[-1]
            if reference_of(column) in [prop, f"{cls.normalized_name()}.{prop}"]:
                foreign_tables.extend([t.__table__ for t in tables])
                if column.table is not cls.__table__:
                    foreign_tables.append(column.table)
                return column
        raise Unsearchable(prop, cls)

    @classmethod
    def pk_values_to_dict(cls, *pk_values) -> dict[str, Any]:
        """
        Converts the primary key values to a dictionary.

        :param pk_values: The primary key values, in order
        :return: A new dict containing the primary key values
        """
        return dict(zip(cls.get_pk_names(), *pk_values))

    def copy_model(self, source: Self, *fields: str) -> None:
        """Copies values from another instance of this Model.

        Unless the fields are specified, all but PK are copied.

        :param source: The model instance from which to copy values
        :param fields: The names of fields to copy
        """
        if fields:
            values = source.model_dump(include=set(fields))
        else:
            values = source.model_dump(exclude=set(source.get_pk_names()))
        self.set_values(**values)

    def set_values(self, ignore_pk: Optional[bool] = False, **values) -> None:
        """Copies property values to this Model.

        By default, Primary Key values are set if present within the values.

        :param ignore_pk: True if you also wish to not set Primary Key values
        :param values: The dict including values to set
        """
        values = retain_in_dict(values, *names_of(self.get_properties()))
        if ignore_pk:
            values = remove_from_dict(values, *self.get_pk_names())
        for k, v in values.items():
            setattr(self, k, v)

    def __eq__(self, other: Self):
        """Instances are determined to be equal based on only their primary key."""
        return self.get_pk_values() == other.get_pk_values() if type(self) == type(other) else False

    def __hash__(self):
        return hash(self.get_pk_values())

    def __str__(self):
        """
        str representation of this is a str of the primary key.
        A single-column PK results in a simple str value of said column i.e. "1234"
        A multi-column PK results in a str of tuple of PK values i.e. ("Cod", "123 Lake Way")
        """
        pk_values = self.get_pk_values()
        if len(pk_values) == 1:
            pk_values = pk_values[0]
        return str(pk_values)


class Unsearchable(Exception):
    """Indicates that the Search Query is not allowed for the specified field."""
    def __init__(self, prop: str, model: type(DAOModel)):
        self.detail = f"Cannot search for {prop} of {model.doc_name()}"


def all_models(bind: Union[Engine, Connection]) -> set[type[DAOModel]]:
    """
    Discovers all DAOModel types that have been created for the database.

    :param bind: The Engine or Connection for the DB
    :return: A set of applicable DAOModels
    """
    def daomodel_subclasses(cls):
        """Returns all defined DAOModels"""
        subclasses = set(cls.__subclasses__())
        for subclass in subclasses.copy():
            subclasses.update(daomodel_subclasses(subclass))
        return subclasses

    metadata = MetaData()
    metadata.reflect(bind=bind)
    db_tables = metadata.tables.keys()
    return {model for model in daomodel_subclasses(DAOModel) if model.__tablename__ in db_tables}


PrimaryKey = Field(primary_key=True)
OptionalPrimaryKey = Field(primary_key=True, default=None)


def PrimaryForeignKey(foreign_property: str) -> Field:
    """Shortcut for creating a Field that is both a PrimaryKey and ForeignKey.

    :param foreign_property: The table/column reference for the foreign key
    :return: The SQLModel Field object defining the sa_column
    """
    return ForeignKey(foreign_property, primary=True)


_sentinel = object()

def ForeignKey(foreign_property: str,
               default: Optional[Any] = _sentinel,
               ondelete: Optional[str] = 'CASCADE',
               primary: Optional[bool] = False) -> Field:
    """Shortcut for creating a Field that is a ForeignKey.

    Deletions and updates are automatically set to cascade.

    :param foreign_property: The table/column reference for the foreign key
    :param default: An optional default value for the field
    :param ondelete: As defined by SQLAlchemy, valid options include SET NULL and RESTRICT. It is CASCADE by default
    :param primary: True if this field is also a primary key
    :return: The SQLModel Field object defining the sa_column
    """
    sa_column = Column(sqlalchemy.ForeignKey(foreign_property, ondelete=ondelete, onupdate='CASCADE'),
                       primary_key=primary)
    return Field(sa_column=sa_column) if default is _sentinel else Field(default=default, sa_column=sa_column)


def OptionalForeignKey(foreign_property: str, primary: Optional[bool] = False) -> Field:
    """Shortcut for creating a Field that is a ForeignKey.

    If the reference is deleted, this field will be set to NULL.

    :param foreign_property: The table/column reference for the foreign key
    :param primary: True if this field is also a primary key
    :return: The SQLModel Field object defining the sa_column
    """
    return ForeignKey(foreign_property, ondelete='SET NULL', primary=primary)
