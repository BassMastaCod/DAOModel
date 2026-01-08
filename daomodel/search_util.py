from typing import Optional, TypeVar, Generic

from pydantic_core import core_schema
from sqlalchemy import ColumnElement
from sqlmodel import or_, and_, extract


T = TypeVar('T')

class ConditionOperator(Generic[T]):
    target_type: type | None = None

    def __class_getitem__(cls, item: type[T]):
        return type(
            f'{cls.__name__}[{item.__name__}]',
            (cls,),
            {'target_type': item}
        )

    """A utility class to easily generate common expressions"""
    def __init__(self, *values: T, _part: Optional[str] = None):
        self.values = values
        self.part = _part  # e.g. "year", "month", "day", "hour"

    def target(self, column: ColumnElement) -> ColumnElement:
        """Return either the column itself or a datetime part expression."""
        if self.part:
            return extract(self.part, column)
        return column

    def get_expression(self, column: ColumnElement) -> ColumnElement:
        """Builds and returns the appropriate expression.

        :param column: The column on which to evaluate
        :return: the expression
        """
        raise NotImplementedError('Must implement `get_expression` in subclass')

    @classmethod
    def __get_pydantic_core_schema__(cls, source, _handler):
        target_type = cls.target_type or str

        def validate(value):
            if isinstance(value, str):
                return cls.from_str(value)
            elif isinstance(value, target_type):
                return Equals(value)
            else:
                raise ValueError(f'Invalid value for {source}: {value}')

        return core_schema.json_or_python_schema(
            json_schema=(
                core_schema.int_schema() if target_type is int else
                core_schema.float_schema() if target_type is float else
                core_schema.bool_schema() if target_type is bool else
                core_schema.str_schema() if target_type is str else
                core_schema.str_schema() if target_type.__name__ in ('datetime', 'date') else
                core_schema.str_schema() if target_type.__name__ == 'UUID' else
                core_schema.str_schema()
            ),
            python_schema=core_schema.no_info_plain_validator_function(validate)
        )

    @classmethod
    def from_str(cls, value: str) -> 'ConditionOperator':
        """Maps a value with a potential operator prefix (e.g. 'lt:', 'contains:') to a ConditionOperator.

        :param value: The query value with optional operator prefix
        :return: The ConditionOperator defined by the prefix
        """
        target_type = cls.target_type or str
        op, part = None, None

        if ':' in value:
            op, value = value.split(':', 1)
            if '_' in op:
                part, op = op.split('_', 1)

        def cast(v):
            return int(v) if part else target_type(v)

        match op:  # TODO: support contains, starts, and ends
            case 'lt':
                return LessThan(cast(value), _part=part)
            case 'le':
                return LessThanEqualTo(cast(value), _part=part)
            case 'gt':
                return GreaterThan(cast(value), _part=part)
            case 'ge':
                return GreaterThanEqualTo(cast(value), _part=part)
            case 'between':
                values = [cast(value) for value in value.split('|', 1)]
                return Between(*values, _part=part)
            case 'anyof':
                values = [cast(value) for value in value.split('|')]
                return AnyOf(*values, _part=part)
            case 'noneof':
                values = [cast(value) for value in value.split('|')]
                return NoneOf(*values, _part=part)
            case 'is':
                match value:
                    case 'set':
                        return IsSet()
                    case 'notset':
                        return NotSet()
                    case _:
                        return Equals(cast(value), _part=part)
            case _:
                return Equals(cast(value), _part=part)


class And(ConditionOperator):
    """Combine multiple ConditionOperators with AND."""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return and_(*[operator.get_expression(column) for operator in self.values])


class Or(ConditionOperator):
    """Combine multiple ConditionOperators with OR."""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return or_(*[operator.get_expression(column) for operator in self.values])


class GreaterThan(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return self.target(column) > self.values[0]


class GreaterThanEqualTo(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return self.target(column) >= self.values[0]


class LessThan(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return self.target(column) < self.values[0]


class LessThanEqualTo(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return self.target(column) <= self.values[0]


class Between(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        lower_bound, upper_bound = self.values
        return and_(self.target(column) >= lower_bound,
                    self.target(column) <= upper_bound)


class After(GreaterThan):
    """Alias for GreaterThan, improves readability for datetime comparisons."""
    pass


class Before(LessThan):
    """Alias for LessThan, improves readability for datetime comparisons."""
    pass


class Equals(ConditionOperator):
    """Match rows where column (or part) equals a value."""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return self.target(column) == self.values[0]


class NotEquals(ConditionOperator):
    """Match rows where column (or part) does not equal a value."""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return self.target(column) != self.values[0]


class AnyOf(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return or_(*[self.target(column) == value for value in self.values])


class NoneOf(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return and_(*[self.target(column) != value for value in self.values])


class IsSet(ConditionOperator):
    """Expression to filter to rows that have a value set for a specific Column"""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        col = self.target(column)
        return or_(col == True, and_(col != None, col != False))


class NotSet(ConditionOperator):
    """Expression to filter to rows that have no value set for a specific Column"""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        col = self.target(column)
        return or_(col == False, col == None)


is_set = IsSet()
not_set = NotSet()
