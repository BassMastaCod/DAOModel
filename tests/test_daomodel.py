from typing import Iterable, Union

import pytest
from sqlalchemy import Column
from sqlmodel import Field

from daomodel import DAOModel, names_of, Unsearchable, reference_of
from tests.labeled_tests import labeled_tests


class Model(DAOModel):
    pass


class SimpleModel(DAOModel, table=True):
    pkA: int = Field(primary_key=True)

simple_instance = SimpleModel(pkA=23)


class ForeignKEYModel(DAOModel, table=True):
    pkB: int = Field(primary_key=True)
    prop: str
    fk: int = Field(foreign_key='simple_model.pkA')


class ComplicatedModel(DAOModel, table=True):
    pkC: int = Field(primary_key=True)
    pkD: int = Field(primary_key=True)
    prop1: str
    prop2: str
    fkA: int = Field(foreign_key='simple_model.pkA')
    fkB: int = Field(foreign_key='foreign_key_model.pkB')

    @classmethod
    def get_searchable_properties(cls) -> set[Column|tuple[DAOModel, ..., Column]]:
        return {cls.pkC, cls.pkD, cls.prop1, cls.fkA, cls.fkB, ForeignKEYModel.prop, (ForeignKEYModel, SimpleModel.pkA)}

complicated_instance = ComplicatedModel(pkC=17, pkD=76, prop1='prop', prop2='erty', fkA=23, fkB=32)


class MultiForeignKEYModel(DAOModel, table=True):
    fkC: int = Field(primary_key=True, foreign_key='complicated_model.pkC')
    fkD: int = Field(primary_key=True, foreign_key='complicated_model.pkD')
    fk_prop: str = Field(foreign_key='foreign_key_model.prop')


def test_tablename():
    assert SimpleModel.__tablename__ == 'simple_model'
    assert ForeignKEYModel.__tablename__ == 'foreign_key_model'


@labeled_tests({
    'true': [
        (SimpleModel, SimpleModel.pkA, True),
        (ForeignKEYModel, ForeignKEYModel.pkB, True),
        (ForeignKEYModel, ForeignKEYModel.prop, True),
        (ForeignKEYModel, ForeignKEYModel.fk, True),
        (ComplicatedModel, ComplicatedModel.pkC, True),
        (ComplicatedModel, ComplicatedModel.pkD, True),
        (ComplicatedModel, ComplicatedModel.prop1, True),
        (ComplicatedModel, ComplicatedModel.prop2, True),
        (ComplicatedModel, ComplicatedModel.fkA, True),
        (ComplicatedModel, ComplicatedModel.fkB, True),
        (MultiForeignKEYModel, MultiForeignKEYModel.fkC, True),
        (MultiForeignKEYModel, MultiForeignKEYModel.fkD, True),
        (MultiForeignKEYModel, MultiForeignKEYModel.fk_prop, True)
    ],
    'false': [
        (SimpleModel, ForeignKEYModel.pkB, False),
        (SimpleModel, ForeignKEYModel.prop, False),
        (SimpleModel, ComplicatedModel.pkC, False),
        (SimpleModel, ComplicatedModel.pkD, False),
        (SimpleModel, ComplicatedModel.prop1, False),
        (SimpleModel, ComplicatedModel.prop2, False),
        (SimpleModel, ComplicatedModel.fkB, False),
        (SimpleModel, MultiForeignKEYModel.fk_prop, False),
        (ForeignKEYModel, ComplicatedModel.pkC, False),
        (ForeignKEYModel, ComplicatedModel.pkD, False),
        (ForeignKEYModel, ComplicatedModel.prop1, False),
        (ForeignKEYModel, ComplicatedModel.prop2, False),
        (ForeignKEYModel, ComplicatedModel.fkA, False),
        (ForeignKEYModel, MultiForeignKEYModel.fkC, False),
        (ForeignKEYModel, MultiForeignKEYModel.fkD, False),
        (ComplicatedModel, ForeignKEYModel.prop, False),
        (ComplicatedModel, MultiForeignKEYModel.fk_prop, False),
        (MultiForeignKEYModel, SimpleModel.pkA, False),
        (MultiForeignKEYModel, ComplicatedModel.prop1, False),
        (MultiForeignKEYModel, ComplicatedModel.prop2, False),
        (MultiForeignKEYModel, ComplicatedModel.fkA, False),
        (MultiForeignKEYModel, ComplicatedModel.fkB, False)
    ],
    'foreign keys': [
        (ForeignKEYModel, SimpleModel.pkA, False),
        (ComplicatedModel, SimpleModel.pkA, False),
        (ComplicatedModel, ForeignKEYModel.pkB, False),
        (MultiForeignKEYModel, ComplicatedModel.pkC, False),
        (MultiForeignKEYModel, ComplicatedModel.pkD, False),
        (MultiForeignKEYModel, ForeignKEYModel.prop, False)
    ],
    'foreign references': [
        (SimpleModel, ForeignKEYModel.fk, False),
        (ForeignKEYModel, ComplicatedModel.fkB, False),
        (ForeignKEYModel, MultiForeignKEYModel.fk_prop, False),
        (ComplicatedModel, MultiForeignKEYModel.fkC, False),
        (ComplicatedModel, MultiForeignKEYModel.fkD, False)
    ]
})
def test_has_column(model: DAOModel, column: Column, expected: bool):
    assert model.has_column(column) == expected


@labeled_tests({
    'single word':
        (Model, 'model'),
    'multiple words': [
        (SimpleModel, 'simple_model'),
        (ComplicatedModel, 'complicated_model')
    ],
    'acronym': [
        (ForeignKEYModel, 'foreign_key_model'),
        (MultiForeignKEYModel, 'multi_foreign_key_model')
    ]
})
def test_normalized_name(model: type[DAOModel], expected: str):
    assert model.normalized_name() == expected


@labeled_tests({
    'single word':
        (Model, 'Model'),
    'multiple words': [
        (SimpleModel, 'Simple Model'),
        (ComplicatedModel, 'Complicated Model')
    ],
    'acronym': [
        (ForeignKEYModel, 'Foreign Key Model'),
        (MultiForeignKEYModel, 'Multi Foreign Key Model')
    ]
})
def test_doc_name(model: type[DAOModel], expected: str):
    assert model.doc_name() == expected


@labeled_tests({
    'single column':
        (SimpleModel, ['pkA']),
    'multiple columns':
        (ComplicatedModel, ['pkC', 'pkD'])
})
def test_get_pk_names__single_column(model: type[DAOModel], expected: list[str]):
    assert model.get_pk_names() == expected


@labeled_tests({
    'single column':
        (simple_instance, (23,)),
    'multiple columns':
        (complicated_instance, (17, 76))
})
def test_get_pk_values(model: DAOModel, expected: tuple[int]):
    assert model.get_pk_values() == expected


@labeled_tests({
    'single column':
        (simple_instance, {'pkA': 23}),
    'multiple columns':
        (complicated_instance, {'pkC': 17, 'pkD': 76})
})
def test_get_pk_dict(model: DAOModel, expected: dict[str, int]):
    assert model.get_pk_dict() == expected


@labeled_tests({
    'single column':
        (ForeignKEYModel, {'pkA'}),
    'multiple columns':
        (ComplicatedModel, {'pkA', 'pkB'})
})
def test_get_fks(model: type[DAOModel], expected: set[str]):
    assert set(names_of(model.get_fks())) == expected


@labeled_tests({
    'single column':
        (ForeignKEYModel, {'fk'}),
    'multiple columns':
        (ComplicatedModel, {'fkA', 'fkB'})
})
def test_get_fk_properties(model: type[DAOModel], expected: set[str]):
    assert set(names_of(model.get_fk_properties())) == expected


def to_str(columns: Iterable[Column]):
    """Converts columns to strings instead to make assert comparisons simpler"""
    return {reference_of(column) for column in columns}


@labeled_tests({
    'single column':
        (ForeignKEYModel, SimpleModel, {ForeignKEYModel.fk}),
    'some applicable columns': [
        (ComplicatedModel, SimpleModel, {ComplicatedModel.fkA}),
        (ComplicatedModel, ForeignKEYModel, {ComplicatedModel.fkB})
    ],
    'no applicable columns':
        (MultiForeignKEYModel, SimpleModel, {}),
    'non primary key':
        (MultiForeignKEYModel, ForeignKEYModel, {MultiForeignKEYModel.fk_prop}),
    'multiple columns':
        (MultiForeignKEYModel, ComplicatedModel, {MultiForeignKEYModel.fkC, MultiForeignKEYModel.fkD})
})
def test_get_references_of(model: type[DAOModel], reference: type[DAOModel], expected: set[Column]):
    assert to_str(model.get_references_of(reference)) == to_str(expected)


@labeled_tests({
    'single column':
        (SimpleModel, ['pkA']),
    'multiple columns':
        (ComplicatedModel, ['pkC', 'pkD', 'prop1', 'prop2', 'fkA', 'fkB'])
})
def test_get_properties(model: type[DAOModel], expected: list[str]):
    assert names_of(model.get_properties()) == expected


@labeled_tests({
    'single column':
        (SimpleModel, ['pkA']),
    'multiple columns':
        (ForeignKEYModel, ['pkB', 'prop', 'fk'])
})
def test_get_searchable_properties__single_column(model: type[DAOModel], expected: list[str]):
    assert names_of(model.get_searchable_properties()) == expected


@labeled_tests({
    'column': [
        (ComplicatedModel.pkC, []),
        (ComplicatedModel.pkD, []),
        (ComplicatedModel.prop1, []),
        (ComplicatedModel.fkA, []),
        (ComplicatedModel.fkB, [])
    ],
    'column reference': [
        ('complicated_model.pkC', []),
        ('complicated_model.pkD', []),
        ('complicated_model.prop1', []),
        ('complicated_model.fkA', []),
        ('complicated_model.fkB', [])
    ],
    'column name': [
        ('pkC', []),
        ('pkD', []),
        ('prop1', []),
        ('fkA', []),
        ('fkB', [])
    ],
    'foreign property': [
        (ForeignKEYModel.prop, [ForeignKEYModel.normalized_name()]),
        ('foreign_key_model.prop', [ForeignKEYModel.normalized_name()])
    ],
    'nested foreign property': [
        (SimpleModel.pkA, [ForeignKEYModel.normalized_name(), SimpleModel.normalized_name()]),
        ('simple_model.pkA', [ForeignKEYModel.normalized_name(), SimpleModel.normalized_name()])
    ]
})
def test_find_searchable_column(prop: Union[str, Column], expected: list[str]):
    foreign_tables = []
    assert ComplicatedModel.find_searchable_column(prop, foreign_tables)
    assert [t.name for t in foreign_tables] == expected


def test_find_searchable_column__foreign_without_table():
    with pytest.raises(Unsearchable):
        assert ComplicatedModel.find_searchable_column('prop', [])


@labeled_tests({
    'single column':
        (SimpleModel, (23,), {'pkA': 23}),
    'multiple columns':
        (ComplicatedModel, (17, 76), {'pkC': 17, 'pkD': 76})
})
def test_pk_values_to_dict__single_column(model: type[DAOModel], args: tuple[int, ...], expected: dict[str, int]):
    assert model.pk_values_to_dict(args) == expected


def test_copy_model():
    other = ComplicatedModel(pkC=12, pkD=34, prop1='different', prop2='values', fkA=1, fkB=2)
    other.copy_model(complicated_instance)
    assert other.pkC == 12
    assert other.pkD == 34
    assert other.prop1 == 'prop'
    assert other.prop2 == 'erty'
    assert other.fkA == 23
    assert other.fkB == 32
    assert complicated_instance.pkC == 17
    assert complicated_instance.pkD == 76
    assert complicated_instance.prop1 == 'prop'
    assert complicated_instance.prop2 == 'erty'
    assert complicated_instance.fkA == 23
    assert complicated_instance.fkB == 32


def test_copy_values():
    other = ComplicatedModel(pkC=12, pkD=34, prop1='different', prop2='values', fkA=1, fkB=2)
    other.copy_values(pkC=0, prop1='new', other='extra')
    assert other.model_dump() == {
        'pkC': 12,
        'pkD': 34,
        'prop1': 'new',
        'prop2': 'values',
        'fkA': 1,
        'fkB': 2
    }


@labeled_tests({
    'single column': (
            simple_instance,
            SimpleModel(pkA=23),
            (
                    SimpleModel(pkA=32),
                    SimpleModel(pkA=45)
            )
    ),
    'multiple columns': (
            complicated_instance,
            ComplicatedModel(pkC=17, pkD=76, prop1='different', prop2='values', fkA=1, fkB=2),
            (
                    ComplicatedModel(pkC=17, pkD=89, prop1='prop', prop2='erty', fkA=23, fkB=32),
                    ComplicatedModel(pkC=17, pkD=89, prop1='prop', prop2='erty', fkA=23, fkB=32)
            )
    )
})
def test___eq____hash__(model: DAOModel, equivalent: DAOModel, different: tuple[DAOModel, ...]):
    assert model == equivalent
    assert hash(model) == hash(equivalent)
    for instance in different:
        assert model != instance
        assert hash(model) != hash(instance)


@labeled_tests({
    'single column':
        (simple_instance, '23'),
    'multiple columns':
        (complicated_instance, '(17, 76)')
})
def test___str___single_column(model: DAOModel, expected: str):
    assert str(model) == expected
