from typing import Any, Iterable

import pytest
from sqlalchemy import Column
from sqlmodel import Field

from daomodel import DAOModel, names_of, Unsearchable, reference_of
from tests.labeled_tests import labeled_tests


class SimpleModel(DAOModel, table=True):
    pkA: int = Field(primary_key=True)

simple_instance = SimpleModel(pkA=23)


class ForeignKEYModel(DAOModel, table=True):
    pkB: int = Field(primary_key=True)
    prop: str
    fkA: int = Field(foreign_key='simple_model.pkA')


class MultiForeignKEYModel(DAOModel, table=True):
    pfk1: int = Field(primary_key=True, foreign_key='complicated_model.pk1')
    pfk2: int = Field(primary_key=True, foreign_key='complicated_model.pk2')
    fk3: str = Field(foreign_key='foreign_key_model.prop')


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


def test_tablename():
    assert SimpleModel.__tablename__ == 'simple_model'
    assert ForeignKEYModel.__tablename__ == 'foreign_key_model'


def test_normalized_name():
    assert SimpleModel.normalized_name() == 'simple_model'
    assert ForeignKEYModel.normalized_name() == 'foreign_key_model'


def test_doc_name():
    assert SimpleModel.doc_name() == 'Simple Model'
    assert ForeignKEYModel.doc_name() == 'Foreign Key Model'


def test_get_pk_names__single_column():
    assert SimpleModel.get_pk_names() == ['pkA']


def test_get_pk_names__multi_column():
    assert ComplicatedModel.get_pk_names() == ['pk1', 'pk2']


def test_get_pk_values__single_column():
    assert simple_instance.get_pk_values() == (23,)


def test_get_pk_values__multi_column():
    assert complicated_instance.get_pk_values() == (17, 76)


def test_get_pk_dict__single_column():
    assert simple_instance.get_pk_dict() == {'pkA': 23}


def test_get_pk_dict__multi_column():
    assert complicated_instance.get_pk_dict() == {'pk1': 17, 'pk2': 76}


def test_get_fks__single_column():
    assert names_of(ForeignKEYModel.get_fks()) == ['pkA']


def test_get_fks__multi_column():
    assert set(names_of(ComplicatedModel.get_fks())) == {'pkA', 'pkB'}


def test_get_fk_properties__single_column():
    assert names_of(ForeignKEYModel.get_fk_properties()) == ['fkA']


def test_get_fk_properties__multi_column():
    assert set(names_of(ComplicatedModel.get_fk_properties())) == {'fk1', 'fk2'}


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
def test_get_references_of(model: DAOModel, reference: DAOModel, expected: set[Column]):
    assert to_str(model.get_references_of(reference)) == to_str(expected)


def test_get_searchable_properties__single_column():
    assert names_of(SimpleModel.get_searchable_properties()) == ['pkA']


def test_get_searchable_properties__multi_column():
    assert set(names_of(ForeignKEYModel.get_searchable_properties())) == {'pkB', 'prop', 'fkA'}


@pytest.mark.parametrize('prop', (
    ComplicatedModel.pk1,
    ComplicatedModel.pk2,
    ComplicatedModel.prop1,
    ComplicatedModel.fk1,
    ComplicatedModel.fk2,
    'complicated_model.pk1',
    'complicated_model.pk2',
    'complicated_model.prop1',
    'complicated_model.fk1',
    'complicated_model.fk2',
    'pk1',
    'pk2',
    'prop1',
    'fk1',
    'fk2'
))
def test_find_searchable_column(prop: str|Any):
    foreign_tables = []
    assert ComplicatedModel.find_searchable_column(prop, foreign_tables)
    assert not foreign_tables


@pytest.mark.parametrize('prop', (
    ForeignKEYModel.prop,
    'foreign_key_model.prop'
))
def test_find_searchable_column__foreign(prop: str|Any):
    foreign_tables = []
    assert ComplicatedModel.find_searchable_column(prop, foreign_tables)
    assert [t.name for t in foreign_tables] == [ForeignKEYModel.normalized_name()]


@pytest.mark.parametrize('prop', (
    SimpleModel.pkA,
    'simple_model.pkA'
))
def test_find_searchable_column__nested_foreign(prop: str|Any):
    foreign_tables = []
    assert ComplicatedModel.find_searchable_column(prop, foreign_tables)
    assert [t.name for t in foreign_tables] == [ForeignKEYModel.normalized_name(), SimpleModel.normalized_name()]


def test_find_searchable_column__foreign_without_table():
    with pytest.raises(Unsearchable):
        assert ComplicatedModel.find_searchable_column('prop', [])


def test_pk_values_to_dict__single_column():
    assert SimpleModel.pk_values_to_dict((23,)) == {'pkA': 23}


def test_pk_values_to_dict__multi_column():
    assert ComplicatedModel.pk_values_to_dict((17, 76)) == {'pk1': 17, 'pk2': 76}


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


def test___eq___single_column():
    assert simple_instance == SimpleModel(pkA=23)
    assert simple_instance != SimpleModel(pkA=32)


def test___eq___multi_column():
    assert complicated_instance == ComplicatedModel(pk1=17, pk2=76, prop1='different', prop2='values', fk1=1, fk2=2)
    assert complicated_instance != ComplicatedModel(pk1=17, pk2=89, prop1='prop', prop2='erty', fk1=23, fk2=32)
    assert complicated_instance != ComplicatedModel(pk1=76, pk2=17, prop1='prop', prop2='erty', fk1=23, fk2=32)


def test___hash___single_column():
    assert hash(simple_instance) == hash(SimpleModel(pkA=23))
    assert hash(simple_instance) != hash(SimpleModel(pkA=32))


def test___hash___multi_column():
    assert hash(complicated_instance) == hash(ComplicatedModel(pk1=17, pk2=76, prop1='different', prop2='values', fk1=1, fk2=2))
    assert hash(complicated_instance) != hash(ComplicatedModel(pk1=17, pk2=89, prop1='prop', prop2='erty', fk1=23, fk2=32))
    assert hash(complicated_instance) != hash(ComplicatedModel(pk1=76, pk2=17, prop1='prop', prop2='erty', fk1=23, fk2=32))


def test___str___single_column():
    assert str(simple_instance) == '23'


def test___str___multi_column():
    assert str(complicated_instance) == '(17, 76)'
