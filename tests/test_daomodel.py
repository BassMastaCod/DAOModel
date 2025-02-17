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
    fkA: int = Field(foreign_key='simple_model.pkA')


class ComplicatedModel(DAOModel, table=True):
    pk1: int = Field(primary_key=True)
    pk2: int = Field(primary_key=True)
    prop1: str
    prop2: str
    fk1: int = Field(foreign_key='simple_model.pkA')
    fk2: int = Field(foreign_key='foreign_key_model.pkB')

    @classmethod
    def get_searchable_properties(cls) -> set[Column|tuple[DAOModel, ..., Column]]:
        return {cls.pk1, cls.pk2, cls.prop1, cls.fk1, cls.fk2, ForeignKEYModel.prop, (ForeignKEYModel, SimpleModel.pkA)}

complicated_instance = ComplicatedModel(pk1=17, pk2=76, prop1='prop', prop2='erty', fk1=23, fk2=32)


class MultiForeignKEYModel(DAOModel, table=True):
    pfk1: int = Field(primary_key=True, foreign_key='complicated_model.pk1')
    pfk2: int = Field(primary_key=True, foreign_key='complicated_model.pk2')
    fk3: str = Field(foreign_key='foreign_key_model.prop')


def test_tablename():
    assert SimpleModel.__tablename__ == 'simple_model'
    assert ForeignKEYModel.__tablename__ == 'foreign_key_model'


@labeled_tests({
    'true': [
        (SimpleModel, SimpleModel.pkA, True),
        (ForeignKEYModel, ForeignKEYModel.pkB, True),
        (ForeignKEYModel, ForeignKEYModel.prop, True),
        (ForeignKEYModel, ForeignKEYModel.fkA, True),
        (ComplicatedModel, ComplicatedModel.pk1, True),
        (ComplicatedModel, ComplicatedModel.pk2, True),
        (ComplicatedModel, ComplicatedModel.prop1, True),
        (ComplicatedModel, ComplicatedModel.prop2, True),
        (ComplicatedModel, ComplicatedModel.fk1, True),
        (ComplicatedModel, ComplicatedModel.fk2, True),
        (MultiForeignKEYModel, MultiForeignKEYModel.pfk1, True),
        (MultiForeignKEYModel, MultiForeignKEYModel.pfk2, True),
        (MultiForeignKEYModel, MultiForeignKEYModel.fk3, True)
    ],
    'false': [
        (SimpleModel, ForeignKEYModel.pkB, False),
        (SimpleModel, ForeignKEYModel.prop, False),
        (SimpleModel, ComplicatedModel.pk1, False),
        (SimpleModel, ComplicatedModel.pk2, False),
        (SimpleModel, ComplicatedModel.prop1, False),
        (SimpleModel, ComplicatedModel.prop2, False),
        (SimpleModel, ComplicatedModel.fk2, False),
        (SimpleModel, MultiForeignKEYModel.fk3, False),
        (ForeignKEYModel, ComplicatedModel.pk1, False),
        (ForeignKEYModel, ComplicatedModel.pk2, False),
        (ForeignKEYModel, ComplicatedModel.prop1, False),
        (ForeignKEYModel, ComplicatedModel.prop2, False),
        (ForeignKEYModel, ComplicatedModel.fk1, False),
        (ForeignKEYModel, MultiForeignKEYModel.pfk1, False),
        (ForeignKEYModel, MultiForeignKEYModel.pfk2, False),
        (ComplicatedModel, ForeignKEYModel.prop, False),
        (ComplicatedModel, MultiForeignKEYModel.fk3, False),
        (MultiForeignKEYModel, SimpleModel.pkA, False),
        (MultiForeignKEYModel, ComplicatedModel.prop1, False),
        (MultiForeignKEYModel, ComplicatedModel.prop2, False),
        (MultiForeignKEYModel, ComplicatedModel.fk1, False),
        (MultiForeignKEYModel, ComplicatedModel.fk2, False)
    ],
    'foreign keys': [
        (ForeignKEYModel, SimpleModel.pkA, False),
        (ComplicatedModel, SimpleModel.pkA, False),
        (ComplicatedModel, ForeignKEYModel.pkB, False),
        (MultiForeignKEYModel, ComplicatedModel.pk1, False),
        (MultiForeignKEYModel, ComplicatedModel.pk2, False),
        (MultiForeignKEYModel, ForeignKEYModel.prop, False)
    ],
    'foreign references': [
        (SimpleModel, ForeignKEYModel.fkA, False),
        (ForeignKEYModel, ComplicatedModel.fk2, False),
        (ForeignKEYModel, MultiForeignKEYModel.fk3, False),
        (ComplicatedModel, MultiForeignKEYModel.pfk1, False),
        (ComplicatedModel, MultiForeignKEYModel.pfk2, False)
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
        (ComplicatedModel, ['pk1', 'pk2'])
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
        (complicated_instance, {'pk1': 17, 'pk2': 76})
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
        (ForeignKEYModel, {'fkA'}),
    'multiple columns':
        (ComplicatedModel, {'fk1', 'fk2'})
})
def test_get_fk_properties(model: type[DAOModel], expected: set[str]):
    assert set(names_of(model.get_fk_properties())) == expected


def to_str(columns: Iterable[Column]):
    """Converts columns to strings instead to make assert comparisons simpler"""
    return {reference_of(column) for column in columns}


@labeled_tests({
    'single column':
        (ForeignKEYModel, SimpleModel, {ForeignKEYModel.fkA}),
    'some applicable columns': [
        (ComplicatedModel, SimpleModel, {ComplicatedModel.fk1}),
        (ComplicatedModel, ForeignKEYModel, {ComplicatedModel.fk2})
    ],
    'no applicable columns':
        (MultiForeignKEYModel, SimpleModel, {}),
    'non primary key':
        (MultiForeignKEYModel, ForeignKEYModel, {MultiForeignKEYModel.fk3}),
    'multiple columns':
        (MultiForeignKEYModel, ComplicatedModel, {MultiForeignKEYModel.pfk1, MultiForeignKEYModel.pfk2})
})
def test_get_references_of(model: type[DAOModel], reference: type[DAOModel], expected: set[Column]):
    assert to_str(model.get_references_of(reference)) == to_str(expected)


@labeled_tests({
    'single column':
        (SimpleModel, ['pkA']),
    'multiple columns':
        (ComplicatedModel, ['pk1', 'pk2', 'prop1', 'prop2', 'fk1', 'fk2'])
})
def test_get_properties(model: type[DAOModel], expected: list[str]):
    assert names_of(model.get_properties()) == expected


@labeled_tests({
    'single column':
        (SimpleModel, ['pkA']),
    'multiple columns':
        (ForeignKEYModel, ['pkB', 'prop', 'fkA'])
})
def test_get_searchable_properties__single_column(model: type[DAOModel], expected: list[str]):
    assert names_of(model.get_searchable_properties()) == expected


@labeled_tests({
    'column': [
        (ComplicatedModel.pk1, []),
        (ComplicatedModel.pk2, []),
        (ComplicatedModel.prop1, []),
        (ComplicatedModel.fk1, []),
        (ComplicatedModel.fk2, [])
    ],
    'column reference': [
        ('complicated_model.pk1', []),
        ('complicated_model.pk2', []),
        ('complicated_model.prop1', []),
        ('complicated_model.fk1', []),
        ('complicated_model.fk2', [])
    ],
    'column name': [
        ('pk1', []),
        ('pk2', []),
        ('prop1', []),
        ('fk1', []),
        ('fk2', [])
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
        (ComplicatedModel, (17, 76), {'pk1': 17, 'pk2': 76})
})
def test_pk_values_to_dict__single_column(model: type[DAOModel], args: tuple[int, ...], expected: dict[str, int]):
    assert model.pk_values_to_dict(args) == expected


def test_copy_model():
    other = ComplicatedModel(pk1=12, pk2=34, prop1='different', prop2='values', fk1=1, fk2=2)
    other.copy_model(complicated_instance)
    assert other.pk1 == 12
    assert other.pk2 == 34
    assert other.prop1 == 'prop'
    assert other.prop2 == 'erty'
    assert other.fk1 == 23
    assert other.fk2 == 32
    assert complicated_instance.pk1 == 17
    assert complicated_instance.pk2 == 76
    assert complicated_instance.prop1 == 'prop'
    assert complicated_instance.prop2 == 'erty'
    assert complicated_instance.fk1 == 23
    assert complicated_instance.fk2 == 32


def test_copy_values():
    other = ComplicatedModel(pk1=12, pk2=34, prop1='different', prop2='values', fk1=1, fk2=2)
    other.copy_values(pk1=0, prop1='new', other='extra')
    assert other.model_dump() == {
        'pk1': 12,
        'pk2': 34,
        'prop1': 'new',
        'prop2': 'values',
        'fk1': 1,
        'fk2': 2
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
            ComplicatedModel(pk1=17, pk2=76, prop1='different', prop2='values', fk1=1, fk2=2),
            (
                    ComplicatedModel(pk1=17, pk2=89, prop1='prop', prop2='erty', fk1=23, fk2=32),
                    ComplicatedModel(pk1=17, pk2=89, prop1='prop', prop2='erty', fk1=23, fk2=32)
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
