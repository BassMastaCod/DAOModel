from __future__ import annotations

from typing import Optional, Any, TypeVar, Iterable, Iterator

from sqlalchemy import func, Column, text, UnaryExpression
from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query

from daomodel.util import values_from_dict, retain_in_dict, MissingInput, InvalidArgumentCount, ensure_iter, dedupe, ConditionOperator
from daomodel.transaction import TransactionMixin

from daomodel import DAOModel


class NotFound(Exception):
    """Indicates that the requested object could not be found."""
    def __init__(self, model: DAOModel):
        self.detail = f'{model.__class__.doc_name()} {model} not found'


class Conflict(Exception):
    """Indicates that the store could not be updated due to an existing conflict."""
    def __init__(self, model: Optional[DAOModel] = None, msg: Optional[str] = None):
        self.detail = msg if msg else f'{model.__class__.doc_name()} {model} already exists'


Model = TypeVar('Model', bound=DAOModel)
class SearchResults(list[Model]):
    """The paginated results of a filtered search."""
    def __init__(self, results: list[Model], total: int = None, page: Optional[int] = None, per_page: Optional[int] = None):
        super().__init__(results)
        self.results = results
        self.total = len(results) if total is None else total
        self.page = page
        self.per_page = per_page

    def __iter__(self) -> Iterator[Model]:
        return iter(self.results)

    def __eq__(self, other: 'SearchResults') -> bool:
        return (self.results == other.results
                and self.total == other.total
                and self.page == other.page
                and self.per_page == other.per_page
                ) if type(self) == type(other) else False

    def __hash__(self) -> int:
        return hash((tuple(self.results), self.total, self.page, self.per_page))

    def __str__(self) -> str:
        string = str(self.results)
        if self.page:
            string = f'Page {self.page}; {self.per_page} of {self.total} results {string}'
        return string

    def first(self) -> Optional[Model]:
        """Returns the first result or None if there are no results"""
        return next(iter(self), None)

    def only(self) -> Optional[Model]:
        """Returns the single result that was found.

        :raises ValueError: If there are no results or more than one result
        """
        if len(self) != 1:
            raise ValueError('Expected exactly one result')
        return self.first()


class DAO(TransactionMixin):
    """A DAO implementation for SQLAlchemy to make your code less SQLly."""
    def __init__(self, model_class: type[Model], db: Session):
        self.model_class = model_class
        self.db = db
        if not hasattr(self.db, '_in_transaction'):
            self.db._in_transaction = False

    @property
    def query(self) -> Query[Any]:
        """Access the SQLAlchemy Query object for full SQLAlchemy functionality.

        :return: The Query for the current Session
        """
        return self.db.query(self.model_class)

    def _check_pk_arguments(self, pk_values: tuple) -> dict[str, Any]:
        """Validates that the number of primary key values matches the expected count.

        :param pk_values: The primary key values to validate (matching the order they are defined in the model)
        :return: A dictionary mapping primary key names to their values
        :raises InvalidArgumentCount: if the provided values do not align with the model's primary key
        """
        keys = self.model_class.get_pk_names()
        if len(pk_values) != len(keys):
            raise InvalidArgumentCount(len(keys), len(pk_values), f'{self.model_class.doc_name()} primary key')
        return {keys[i]: pk_values[i] for i in range(len(keys))}

    def create(self, *pk_values: Any) -> Model:
        """Creates a new entry for the given primary key.

        :param pk_values: Primary key values to represent the Model (in the order defined in the model)
        :return: The DAOModel entry that was newly added to the database
        :raises Conflict: if an entry already exists for the primary key
        :raises InvalidArgumentCount: if the provided values do not align with the model's primary key
        """
        return self.create_with(**self._check_pk_arguments(pk_values))

    def create_with(self, insert: bool = True, **values: Any) -> Model:
        """Creates a new entry for the given primary key and property values.

        :param insert: False to avoid adding the model to the database
        :param values: The values to assign to the model
        :return: The new DAOModel
        :raises Conflict: if an entry already exists for the primary key (does not apply if insert=False)
        """
        model = self.model_class(**retain_in_dict(values, *self.model_class.get_pk_names()))
        model.set_values(ignore_pk=True, **values)
        if insert:
            self.insert(model)
        return model

    def insert(self, model: Model) -> None:
        """Adds the given model to the database.

        :param model: The DAOModel entry to add
        :raises Conflict: if an entry already exists for the primary key
        """
        if self.exists(model):
            raise Conflict(model)
        self.db.add(model)
        if self._auto_commit:
            self.commit()
            self.db.refresh(model)

    def upsert(self, model: Model) -> None:
        """Updates the given model in the database or creates it if it does not exist.

        :param model: The DAOModel entry which may or may not exist
        """
        try:
            self.insert(model)
        except Conflict:
            self.commit()
        return model

    def rename(self, existing: Model, *new_pk_values: Any) -> None:
        """Updates the given model with new primary key values.

        :param existing: The model to rename
        :param new_pk_values: The new primary key values for the model
        :raises Conflict: if an entry already exists for the new primary key
        """
        try:
            raise Conflict(self.get(*new_pk_values))
        except NotFound:
            for k, v in zip(existing.get_pk_names(), new_pk_values):
                setattr(existing, k, v)
            self._commit_if_not_transaction()

    def exists(self, model: Model) -> bool:
        """Determines if a model exists in the database.

        :param model: The DAOModel entry in question
        :return: True if the model exists in the database, False otherwise
        """
        return bool(self.query.filter_by(**model.get_pk_dict()).count())

    def get(self, *pk_values: Any) -> Model:
        """Retrieves an entry from the database by its primary key.

        :param pk_values: The primary key values of the Model to fetch (in the order defined in the model)
        :return: The DAOModel entry that was retrieved
        :raises NotFound: if the model does not exist in the database
        :raises InvalidArgumentCount: if the provided values do not align with the model's primary key
        """
        return self.get_with(**self._check_pk_arguments(pk_values))

    def get_with(self, **values: Any) -> Model:
        """Retrieves an entry from the database and applies the given values to it.

        These changes are not committed to the database. Call commit() to do so.

        :param values: A dictionary containing the pk values of the requested model along with additional values to set
        :return: The DAOModel entry with the additional properties updated
        :raises NotFound: if the model does not exist in the database
        """
        pk = values_from_dict(*self.model_class.get_pk_names(), **values)
        model = self.query.get(pk)
        if model is None:
            raise NotFound(self.model_class(**values))
        model.set_values(ignore_pk=True, **values)
        return model

    def find(self,
             page: Optional[int] = None,
             per_page: Optional[int] = None,
             **filters: Any) -> SearchResults[Model]:
        """Searches all the DAOModel entries to return results.

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
            if key == 'order':  # TODO: rename to avoid collisions with actual column names
                order = self._order(value, foreign_tables)
            elif key == 'duplicate':
                query = self._count(query, value, foreign_tables, 'dupe').where(text(f'dupe.count > 1'))
            elif key == 'unique':
                query = self._count(query, value, foreign_tables, 'uniq').where(text(f'uniq.count <= 1'))
            else:  # TODO: Add logic for is_set and not_set that works for foreign values
                query = self._filter(query, key, value, foreign_tables)

        for table in dedupe(foreign_tables):
            query = query.join(table)

        query = query.order_by(*order)
        query = self.filter_find(query, **filters)

        total = query.count()
        if per_page:
            if not page or page < 1:
                page = 1
            query = query.offset((page - 1) * per_page).limit(per_page)
        elif page:
            raise MissingInput('Must specify how many results per page')

        return SearchResults(query.all(), total, page, per_page)

    def _order(self,
               value: str|Column|UnaryExpression|Iterable[str|Column|UnaryExpression],
               foreign_tables: list[DAOModel]) -> list[Column|UnaryExpression]:
        order = []
        if type(value) is str:
            value = value.split(', ')
        for column in ensure_iter(value):
            if type(column) is UnaryExpression:
                if self.model_class.find_searchable_column(column.element, foreign_tables) is not None:
                    order.append(column)
            else:
                order.append(self.model_class.find_searchable_column(column, foreign_tables))
        return order

    def _count(self, query: Query, prop: str, foreign_tables: list[DAOModel], alias: str) -> Query:
        column = self.model_class.find_searchable_column(prop, foreign_tables)
        subquery = (self.db.query(column, func.count(column).label('count'))
                    .group_by(column)
                    .subquery()
                    .alias(alias))
        return query.join(subquery, column == text(f'{alias}.{column.name}'))

    def _filter(self, query: Query, key: [str|Column], value: Any, foreign_tables: list[type[DAOModel]]) -> Query:
        column = self.model_class.find_searchable_column(key, foreign_tables)
        return query.filter(value.get_expression(column) if isinstance(value, ConditionOperator) else column == value)

    def filter_find(self, query: Query, **filters: Any) -> Query:
        """Overridable function to customize filtering.

        :param query: The session's SQLAlchemy Query
        :param filters: Any provided filter terms
        :return: The newly modified Query
        """
        return query

    def remove(self, model: Model) -> None:
        """Deletes the given model entry from the database.

        :param model: The DAOModel object to be deleted
        :raises NotFound: if the model does not exist in the database
        """
        if self.exists(model):
            self.db.delete(model)
        else:
            raise NotFound(model)
        self._commit_if_not_transaction()
