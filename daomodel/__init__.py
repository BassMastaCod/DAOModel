from typing import Any, Self, Iterable, Union
from sqlmodel import SQLModel
from sqlalchemy import Column, Engine, inspect
from str_case_util import Case
from sqlalchemy.ext.declarative import declared_attr

from daomodel.util import reference_of, names_of, in_order


property_categories = ['all', 'pk', 'fk', 'standard', 'unset', 'defaults', 'none']


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
            elif key is 'standard':
                props = all_properties.difference(self.get_pk_names()).difference(names_of(self.get_fk_properties()))
            else:
                props = all_properties.difference(self.model_dump(**{f'exclude_{key}': True}))

            result = result.union(props) if value else result.difference(props)
        return in_order(result, property_order)

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

    def copy_model(self, source: Self) -> None:
        """
        Copies all values, except the primary key, from another instance of this Model.

        :param source: The model instance from which to copy values
        """
        primary_key = set(source.get_pk_names())
        values = source.model_dump(exclude=primary_key)
        self.copy_values(**values)

    def copy_values(self, **values) -> None:
        """
        Copies all non-pk property values to this Model.

        :param values: The dict including values to copy
        """
        pk = self.get_pk_names()
        properties = names_of(self.get_properties())
        for k, v in values.items():
            if k in properties and k not in pk:
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


def all_models(engine: Engine) -> set[DAOModel]:
    """
    Discovers all DAOModel types that have been created for the database.

    :param engine: The engine used to create the DB
    :return: A set of applicable DAOModels
    """
    def daomodel_subclasses(cls):
        """Returns all defined DAOModels"""
        subclasses = set(cls.__subclasses__())
        for subclass in subclasses.copy():
            subclasses.update(daomodel_subclasses(subclass))
        return subclasses

    db_tables = set(inspect(engine).get_table_names())
    return {model for model in daomodel_subclasses(DAOModel) if model.__tablename__ in db_tables}
