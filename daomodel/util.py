import warnings
from typing import Iterable, Any, OrderedDict

from sqlalchemy import Column, ColumnElement
from sqlmodel import or_, and_


class MissingInput(Exception):
    """Indicates that required information was not provided."""
    def __init__(self, detail: str):
        self.detail = detail


class InvalidArgumentCount(Exception):
    """Indicates that an incorrect number of arguments was provided."""
    def __init__(self, expected: int, got: int, context: str = None):
        self.detail = f'Expected {expected} values, got {got}'
        if context:
            self.detail += f' for {context}'


class UnsupportedFeatureError(Exception):
    """Indicates that a feature is not yet supported.

    If you think the feature should be implemented, please open an issue on GitHub.
    """
    def __init__(self, detail: str):
        self.detail = detail + (' Note: This functionality is not yet supported. '
                                'Please submit a request through GitHub if you would like it implemented.')


def reference_of(column: Column) -> str:
    """
    Prepares a str reference of a column.

    :param column: The column to convert
    :return: The 'table.column' notation of the Column
    """
    return f'{column.table.name}.{column.name}'


def names_of(properties: Iterable[Column]) -> list[str]:
    """
    Reduces Columns to just their names.

    :param properties: A group of Columns
    :return: A list of names matching the order of the Columns provided
    """
    return [p.name for p in properties]


def mode(values: Iterable[Any]) -> Any:
    """Determines the most frequently occurring value within the provided iterable.

    In the case of a tie (multiple values with the same highest frequency),
    the function returns the first value encountered with that frequency.

    :param values: An iterable containing values to evaluate
    :return: The most common value from the provided iterable
    """
    values = list(values)
    return max(values, key=values.count)


def values_from_dict(*keys: Any, **values: Any) -> tuple:
    """Pulls specific values from a dictionary.

    :param keys: The keys to read from the dict
    :param values: The dictionary containing the values
    :return: A tuple of values read from the dict, in the same order as keys
    """
    result = []
    for key in keys:
        if key in values:
            result.append(values[key])
        else:
            raise MissingInput(f'Requested key {key} not found in dictionary')
    return tuple(result)


def retain_in_dict(d: dict[Any, Any], *keys: Any) -> dict[Any, Any]:
    """Filters a dictionary to specified keys.

    The source dict remains unmodified.

    :param d: The dictionary to filter down
    :param keys: The target keys for the new dict
    :return: The reduced values as a new dict
    """
    return {key: d[key] for key in keys if key in d}


def remove_from_dict(d: dict[Any, Any], *keys: Any) -> dict[Any, Any]:
    """Removes specified key/value pairs from a dictionary.

    The source dict remains unmodified.

    :param d: The dictionary to adjust
    :param keys: The keys to remove from the dict
    :return: The modified values as a new dict
    """
    return {k: v for k, v in d.items() if k not in keys}


def ensure_iter(elements: Any):
    """Ensures that the provided argument is iterable.

    Single, non-Iterable items are converted to a single-item list.
    In this context, a str is not considered to be Iterable.

    :param elements: The input that may or may not be Iterable
    :return: The provided Iterable or a single item list
    """
    if not isinstance(elements, Iterable) or type(elements) is str:
        elements = [elements]
    return elements


def dedupe(original: list) -> list:
    """Creates a filtered copy of a list that does not include duplicates.

    :param original: The list to filter
    :return: a new list that maintains order but is guaranteed to have no duplicates
    """
    return list(OrderedDict.fromkeys(original))


def in_order(original: Iterable, order: list) -> list:
    """Returns provided items as an ordered list.

    Repeated items will be deduplicated.
    Items not defined within the order will be excluded.
    The order is allowed to contain extraneous items that aren't applicable to the provided items.

    :param original: The (likely unordered) collection of items
    :param order: The defined order of items
    :return: a new list of the items following the defined order
    """
    return [item for item in order if item in original]


def next_id() -> None:
    """Indicates to the model that an id should be auto-incremented"""
    return None


class ConditionOperator:
    """A utility class to easily generate common expressions"""
    def __init__(self, *values: Any):
        self.values = values

    def get_expression(self, column: ColumnElement) -> ColumnElement:
        """Builds and returns the appropriate expression.

        :param column: The column on which to evaluate
        :return: the expression
        """
        raise NotImplementedError('Must implement `get_expression` in subclass')


class GreaterThan(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return column > self.values[0]


class GreaterThanEqualTo(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return column >= self.values[0]


class LessThan(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return column < self.values[0]


class LessThanEqualTo(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return column <= self.values[0]


class Between(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        lower_bound, upper_bound = self.values
        return and_(column >= lower_bound, column <= upper_bound)


class AnyOf(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return or_(*[column == value for value in self.values])


class NoneOf(ConditionOperator):
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return and_(*[column != value for value in self.values])


class IsSet(ConditionOperator):
    """Expression to filter to rows that have a value set for a specific Column"""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return or_(column == True, and_(column != None, column != False))


class NotSet(ConditionOperator):
    """Expression to filter to rows that have no value set for a specific Column"""
    def get_expression(self, column: ColumnElement) -> ColumnElement:
        return or_(column == False, column == None)


is_set = IsSet()
not_set = NotSet()
