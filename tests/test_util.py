from typing import Any, Iterable

import pytest
from sqlalchemy.testing.schema import Column

from daomodel import reference_of
from daomodel.util import names_of, values_from_dict, ensure_iter, dedupe, in_order, retain_in_dict, \
    remove_from_dict, mode
from tests.labeled_tests import labeled_tests
from tests.school_models import Person, Book


@pytest.mark.parametrize('column, expected', [
    (Person.name, 'person.name'),
    (Person.ssn, 'person.ssn'),
    (Book.owner, 'book.owner')
])
def test_reference_of(column: Column, expected: str):
    assert reference_of(column) == expected


@pytest.mark.parametrize('columns, expected', [
    ([], []),
    ([Column('one')], ['one']),
    ([Column('one'), Column('two'), Column('three')], ['one', 'two', 'three'])
])
def test_names_of(columns: list[Column], expected:  list[str]):
    assert names_of(columns) == expected


@pytest.mark.parametrize('elements, expected', [
    ([1, 2, 2, 3], 2),
    ([1, 1, 2, 2, 3], 1),
    (['a', 'b', 'b', 'c', 'c', 'c'], 'c'),
    ([True, True, False, True], True),
    ([1], 1)
])
def test_mode(elements: list, expected: Any):
    assert mode(elements) == expected


@pytest.mark.parametrize('keys, expected', [
    ((), ()),
    (('b',), (2,)),
    (('a', 'c'), (1, 3)),
    (('b', 'c', 'a'), (2, 3, 1))
])
def test_values_from_dict(keys: tuple[str, ...], expected: tuple):
    assert values_from_dict(*keys, a=1, b=2, c=3) == expected


@pytest.mark.parametrize('keys, expected', [
    ((), {}),
    (('b',), {'b': 2}),
    (('a', 'c'), {'a':1, 'c':3}),
    (('b', 'c', 'a'), {'a':1, 'b':2, 'c':3})
])
def test_retain_in_dict(keys: tuple[str, ...], expected: tuple):
    assert retain_in_dict({'a': 1, 'b': 2, 'c': 3}, *keys) == expected


@pytest.mark.parametrize('keys, expected', [
    ((), {'a':1, 'b':2, 'c':3}),
    (('b',), {'a':1, 'c':3}),
    (('a', 'c'), {'b': 2}),
    (('b', 'c', 'a'), {})
])
def test_remove_from_dict(keys: tuple[str, ...], expected: tuple):
    assert remove_from_dict({'a': 1, 'b': 2, 'c': 3}, *keys) == expected


@pytest.mark.parametrize('elements, expected', [
    ([1, 2, 3], [1, 2, 3]),
    ({1, 2, 3}, {1, 2, 3}),
    ((1, 2, 3), (1, 2, 3)),
    ([], []),
    ({}, {}),
    ((), ()),
    (1, [1]),
    (None, [None]),
    ('element', ['element'])
])
def test_ensure_iter(elements: Any, expected: Iterable[Any]):
    assert ensure_iter(elements) == expected


@pytest.mark.parametrize('elements, expected', [
    ([1, 2, 3], [1, 2, 3]),
    ([1, 1, 2, 2, 3, 3, 3], [1, 2, 3]),
    (['one', 'two', 'two', 'three'], ['one', 'two', 'three']),
    (['one', 1, 'one', 'two', 2, 'three', 2, 'three'], ['one', 1, 'two', 2, 'three']),
    ([], []),
])
def test_dedupe(elements: list, expected: list):
    assert dedupe(elements) == expected

@labeled_tests({
    'empty': [
        (set(), [], []),
        (set(), [1], []),
        ({1}, [], []),
    ],
    'single item': [
        ({1}, [1], [1]),
        ({'a'}, ['a'], ['a'])
    ],
    'multiple items': [
        ({1, 2, 3}, [1, 2, 3], [1, 2, 3]),
        ({1, 2, 3}, [3, 2, 1], [3, 2, 1]),
        ({'a', 'b', 'c'}, ['a', 'b', 'c'], ['a', 'b', 'c']),
        ({'a', 'b', 'c'}, ['c', 'b', 'a'], ['c', 'b', 'a'])
    ],
    'repeated items': [
        ([1, 1, 2, 2, 3, 3], [1, 2, 3], [1, 2, 3]),
        ([1, 1, 2, 2, 3, 3], [3, 2, 1], [3, 2, 1]),
        (['a', 'b', 'c', 'b', 'a'], ['a', 'b', 'c'], ['a', 'b', 'c']),
        (['a', 'b', 'c', 'b', 'a'], ['c', 'b', 'a'], ['c', 'b', 'a']),
        ([True, True, False, True, False, False], [False, True], [False, True])
    ],
    'items missing from order': [
        ({1, 2, 3, 4}, [1, 2, 3], [1, 2, 3]),
        ({1, 2, 3, 4}, [3, 2, 1], [3, 2, 1])
    ],
    'extraneous items in order': [
        ({1, 3}, [1, 2, 3], [1, 3]),
        ({1, 3}, [3, 2, 1], [3, 1])
    ],
    'mixed scenarios': [
        ({4, 1, 1, 3, 4}, [1, 2, 3], [1, 3]),
        ({1, 3, 1, 4}, [3, 2, 1], [3, 1])
    ]
})
def test_in_order(items: Iterable, order: list, expected: list):
    assert in_order(items, order) == expected
