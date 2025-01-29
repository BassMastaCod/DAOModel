from __future__ import annotations

from typing import Optional, Any, TypeVar, Self, Iterable

from sqlalchemy import func, Column, text, UnaryExpression
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query

from daomodel.util import values_from_dict, filter_dict, MissingInput, ensure_iter, dedupe, ConditionOperator

from daomodel import DAOModel


class NotFound(Exception):
    """Indicates that the requested object could not be found."""
    def __init__(self, model: DAOModel):
        self.detail = f"{model.__class__.doc_name()} {model} not found"


class Conflict(Exception):
    """Indicates that the store could not be updated due to an existing conflict."""
    def __init__(self, model: DAOModel):
        self.detail = f"{model.__class__.doc_name()} {model} already exists"


T = TypeVar("T")
class SearchResults(list[T]):
    """The paginated results of a filtered search."""
    def __init__(self, results: list[T], total: int, page: Optional[int] = None, per_page: Optional[int] = None):
        super().__init__(results)
        self.results = results
        self.total = total
        self.page = page
        self.per_page = per_page

    def __iter__(self):
        return iter(self.results)

    def __eq__(self, other: Self):
        return (self.results == other.results
                and self.total == other.total
                and self.page == other.page
                and self.per_page == other.per_page
                ) if type(self) == type(other) else False

    def __hash__(self):
        return hash((tuple(self.results), self.total, self.page, self.per_page))

    def __str__(self):
        string = str(self.results)
        if self.page:
            string = f"Page {self.page}; {self.per_page} of {self.total} results {string}"
        return string

    def first(self):
        """Returns the first result or None if there are no results"""
        return next(iter(self), None)


class DAO:
    """A DAO implementation for SQLAlchemy to make your code less SQLly."""
    def __init__(self, model_class: type[T], db: Session):
        self.model_class = model_class
        self.db = db

    @property
    def query(self) -> Query[Any]:
        """
        Access the SQLAlchemy Query object for full SQLAlchemy functionality.

        :return: The Query for the current Session
        """
        return self.db.query(self.model_class)

    def create(self, *pk_values) -> T:
        """
        Creates a new entry for the given primary key.

        :param pk_values: The array of primary key values representing the Model
        :return: The DAOModel entry that was newly added to the database
        :raises: Conflict if an entry already exists for the primary key
        """
        return self.create_with(**self.model_class.pk_values_to_dict(pk_values))

    def create_with(self, commit: bool = True, **values) -> T:
        """
        Creates a new entry for the given primary key and property values.

        :param commit: False to avoid adding the model to the database at this time
        :param values: The values to assign to the model
        :return: The new DAOModel
        :raises: Conflict if an entry already exists for the primary key
        """
        model = self.model_class(**filter_dict(*self.model_class.get_pk_names(), **values))
        model.copy_values(**values)
        if commit:
            self.insert(model)
        return model

    def insert(self, model: T) -> None:
        """
        Adds the given model to the database.

        :param model: The DAOModel entry to add
        :raises: Conflict if an entry already exists for the primary key
        """
        if self.exists(model):
            raise Conflict(model)
        self.db.add(model)
        self.commit()
        self.db.refresh(model)

    def update(self, model: T) -> None:
        """
        Updates the database to align with the provided model.

        :param model: The existing DAOModel entry to update in the database
        :raises NotFound: if the model does not exist in the database
        """
        if not self.exists(model):
            raise NotFound(model)
        self.commit()
        self.db.refresh(model)

    def upsert(self, model: T) -> None:
        """
        Updates the given model in the database or creates it if it does not exist.

        :param model: The DAOModel entry which may or may not exist
        """
        try:
            self.update(model)
        except NotFound:
            self.insert(model)
        return model

    def exists(self, model: T) -> bool:
        """
        Determines if a model exists in the database.

        :param model: The DAOModel entry in question
        :return: True if the model exists in the database, False otherwise
        """
        return bool(self.query.filter_by(**model.get_pk_dict()).count())

    def get(self, *pk_values) -> T:
        """
        Retrieves an entry from the database.

        :param pk_values: A dictionary containing the primary key values of the model to get.
        :return: The DAOModel entry that was retrieved
        :raises NotFound: if the model does not exist in the database
        :raises MissingInput: if the provided values do not align with the model's primary key
        """
        keys = self.model_class.get_pk_names()
        if len(pk_values) != len(keys):
            raise MissingInput(f"Expected {len(keys)} values, got {len(pk_values)}")
        return self.get_with(**{keys[i]: pk_values[i] for i in range(len(keys))})

    def get_with(self, **values) -> T:
        """
        Retrieves an entry from the database and applies the given values to it.

        :param values: A dictionary containing the primary key values of the model to get and additional values to set
        :return: The DAOModel entry with the additional properties updated
        :raises NotFound: if the model does not exist in the database
        """
        pk = values_from_dict(*self.model_class.get_pk_names(), **values)
        model = self.query.get(pk)
        if model is None:
            raise NotFound(self.model_class(**values))
        model.copy_values(**values)
        return model

    def find(self,
             page: Optional[int] = None,
             per_page: Optional[int] = None,
             **filters) -> SearchResults[T]:
        """
        Searches all the DAOModel entries to return results.

        :param page: The number of the page to fetch
        :param per_page: How many results are on each page
        :param filters: Criteria to filter down the number of results
        :return: The SearchResults for the provided filters
        """
        query = self.query
        order = self.model_class.get_pk()
        foreign_tables = []

        # TODO: Add support for checking for specific values within foreign tables
        for key, value in filters.items():
            if key == "order":  # TODO: rename to avoid collisions with actual column names
                order = self._order(value, foreign_tables)
            elif key == "duplicate":
                query = self._count(query, value, foreign_tables, "dupe").where(text(f"dupe.count > 1"))
            elif key == "unique":
                query = self._count(query, value, foreign_tables, "uniq").where(text(f"uniq.count <= 1"))
            else:  # TODO: Add logic for is_set and not_set
                query = self._filter(query, key, value, foreign_tables)

        for table in dedupe(foreign_tables):
            query = query.join(table)

        query = query.order_by(*order)
        query = self.filter_find(query, **filters)

        print(query)

        total = query.count()
        if page or per_page:
            if not page:
                page = 1
            elif not per_page:
                raise MissingInput("Must specify how many results per page")
            query = query.offset((page - 1) * per_page).limit(per_page)

        return SearchResults(query.all(), total, page, per_page)

    def _order(self,
               value: str|Column|UnaryExpression|Iterable[str|Column|UnaryExpression],
               foreign_tables: list[DAOModel]) -> list[Column|UnaryExpression]:
        order = []
        if type(value) is str:
            value = value.split(", ")
        for column in ensure_iter(value):
            if type(column) is UnaryExpression:
                if self.model_class.find_searchable_column(column.element, foreign_tables) is not None:
                    order.append(column)
            else:
                order.append(self.model_class.find_searchable_column(column, foreign_tables))
        return order

    def _count(self, query: Query, prop: str, foreign_tables: list[DAOModel], alias: str):
        column = self.model_class.find_searchable_column(prop, foreign_tables)
        subquery = (self.db.query(column, func.count(column).label("count"))
                    .group_by(column)
                    .subquery()
                    .alias(alias))
        return query.join(subquery, column == text(f"{alias}.{column.name}"))

    def _filter(self, query, key, value, foreign_tables):
        column = self.model_class.find_searchable_column(key, foreign_tables)
        return query.filter(value.get_expression(column) if isinstance(value, ConditionOperator) else column == value)

    def filter_find(self, query: Query, **filters) -> Query:
        """
        Overridable function to customize filtering.

        :param query: The session's SQLAlchemy Query
        :param filters: Any provided filter terms
        :return: The newly modified Query
        """
        return query

    def remove(self, model: T, commit: bool = True) -> None:
        """
        Deletes the given model entry from the database.

        :param model: The DAOModel object to be deleted
        :param commit: False to not yet commit
        :raises NotFound: if the model does not exist in the database
        """
        if self.exists(model):
            self.db.delete(model)
        else:
            raise NotFound(model)
        if commit:
            self.commit()

    def commit(self) -> None:
        """
        Commits all pending changes to the database.
        Following commit, DAOModels will need to be re-fetched.
        """
        self.db.commit()
