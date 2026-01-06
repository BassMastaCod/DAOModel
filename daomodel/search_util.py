from typing import Any, Optional

from sqlalchemy import ColumnElement
from sqlmodel import or_, and_, extract


class ConditionOperator:
    """A utility class to easily generate common expressions"""
    def __init__(self, *values: Any, _part: Optional[str] = None):
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
