from typing import Any, Iterable

import pytest
from sqlalchemy.testing.schema import Column

from daomodel import reference_of
from daomodel.util import to_bool, NotBoolValue, names_of, values_from_dict, filter_dict, MissingInput, either, \
    ensure_iter, dedupe
from tests.conftest import Person, Book


@pytest.mark.parametrize("column, expected", [
    (Person.name, "person.name"),
    (Person.ssn, "person.ssn"),
    (Book.owner, "book.owner")
])
def test_reference_of(column: Column, expected:  str):
    assert reference_of(column) == expected


@pytest.mark.parametrize("columns, expected", [
    ([], []),
    ([Column("one")], ["one"]),
    ([Column("one"), Column("two"), Column("three")], ["one", "two", "three"])
])
def test_names_of(columns: list[Column], expected:  list[str]):
    assert names_of(columns) == expected


@pytest.mark.parametrize("keys, expected", [
    ((), ()),
    (("b",), (2,)),
    (("a", "c"), (1, 3)),
    (("b", "c", "a"), (2, 3, 1))
])
def test_values_from_dict(keys: tuple[str], expected: tuple[Any]):
    assert values_from_dict(*keys, a=1, b=2, c=3) == expected


@pytest.mark.parametrize("keys, dictionary", [
    (("a",), {}),
    (("b", ), {"a":1, "c":3}),
    (("b", "c"), {"a":1, "b":2})
])
def test_values_from_dict__missing(keys: tuple[str], dictionary: dict[str, Any]):
    with pytest.raises(MissingInput):
        values_from_dict("missing")


@pytest.mark.parametrize("keys, expected", [
    ((), {}),
    (("b",), {"b": 2}),
    (("a", "c"), {"a":1, "c":3}),
    (("b", "c", "a"), {"a":1, "b":2, "c":3})
])
def test_filter_dict(keys: tuple[str], expected: tuple[Any]):
    assert filter_dict(*keys, a=1, b=2, c=3) == expected


@pytest.mark.parametrize("keys, dictionary", [
    (("a",), {}),
    (("b", ), {"a":1, "c":3}),
    (("b", "c"), {"a":1, "b":2})
])
def test_filter_dict__missing(keys: tuple[str], dictionary: dict[str, Any]):
    with pytest.raises(KeyError):
        filter_dict("missing")


@pytest.mark.parametrize("string", ["false", "False", "FALSE", "fAlSe", "no", "No", "NO", "nO"])
def test_to_bool__str_false(string: str):
    assert not to_bool(string)


@pytest.mark.parametrize("string", ["true", "True", "TRUE", "tRuE", "yes", "Yes", "YES", "yEs"])
def test_to_bool__str_true(string: str):
    assert to_bool(string)


@pytest.mark.parametrize("number, expected", [(0, False), (1, True)])
def test_to_bool__number(number: int, expected: bool):
    assert to_bool(number) == expected


@pytest.mark.parametrize("boolean, expected", [(False, False), (True, True)])
def test_to_bool__bool(boolean: int, expected: bool):
    assert to_bool(boolean) == expected


@pytest.mark.parametrize("value", ["", "bool", -1, 100, None])
def test_to_bool__not_bool_value(value: Any):
    with pytest.raises(NotBoolValue):
        to_bool(value)


@pytest.mark.parametrize("preferred, default, expected", [
    (1, 2, 1),
    (0, 1, 0),
    (None, 1, 1),
    (False, True, False),
    (None, True, True),
    ("preferred", "default", "preferred"),
    ("", "default", ""),
    (None, "default", "default"),
    ([1, 2], [3, 4, 5], [1, 2]),
    ([], [3, 4, 5], []),
    (None, [3, 4, 5], [3, 4, 5]),
    (None, None, None)
])
def test_either(preferred: Any, default: Any, expected: Any):
    assert either(preferred, default) == expected


@pytest.mark.parametrize("elements, expected", [
    ([1, 2, 3], [1, 2, 3]),
    ({1, 2, 3}, {1, 2, 3}),
    ((1, 2, 3), (1, 2, 3)),
    ([], []),
    ({}, {}),
    ((), ()),
    (1, [1]),
    (None, [None]),
    ("element", ["element"])
])
def test_ensure_iter(elements: Any, expected: Iterable[Any]):
    assert ensure_iter(elements) == expected


@pytest.mark.parametrize("elements, expected", [
    ([1, 2, 3], [1, 2, 3]),
    ([1, 1, 2, 2, 3, 3, 3], [1, 2, 3]),
    (["one", "two", "two", "three"], ["one", "two", "three"]),
    (["one", 1, "one", "two", 2, "three", 2, "three"], ["one", 1, "two", 2, "three"]),
    ([], []),
])
def test_dedupe(elements: list, expected: list):
    assert dedupe(elements) == expected
