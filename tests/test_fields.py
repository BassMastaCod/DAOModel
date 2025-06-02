from typing import Optional

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field

from daomodel import DAOModel, names_of
from daomodel.fields import Identifier
from tests.conftest import TestDAOFactory


class TestModel(DAOModel, table=True):
    id: Identifier[str]


class CompositeKeyModel(DAOModel, table=True):
    id1: Identifier[int]
    id2: Identifier[int]


class ModelWithOptionalPk(DAOModel, table=True):
    id: Identifier[Optional[int]]
    name: Optional[str]


class ModelWithForeignKey(DAOModel, table=True):
    id: Identifier[int]
    other_id: TestModel


class ModelWithOptionalFk(DAOModel, table=True):
    id: Identifier[int]
    other_id: Optional[TestModel]


class ModelWithPrimaryForeignKey(DAOModel, table=True):
    other_id: Identifier[TestModel]


class ModelWithCustomOnDelete(DAOModel, table=True):
    id: Identifier[int]
    other_id: TestModel = Field(foreign_key='test_model.id', ondelete='RESTRICT')


def test_identifier():
    assert TestModel.get_pk_names() == ['id']


def test_primary_key__composite():
    assert CompositeKeyModel.get_pk_names() == ['id1', 'id2']


def test_primary_key__required(daos: TestDAOFactory):
    dao = daos[TestModel]
    entry = dao.create_with(insert=False)
    with pytest.raises(IntegrityError):
        dao.insert(entry)


def test_primary_key__optional(daos: TestDAOFactory):
    dao = daos[ModelWithOptionalPk]
    assert dao.find().total == 0
    dao.create_with()
    assert dao.find().first().name is None


def test_foreign_key():
    assert names_of(ModelWithForeignKey.get_fks()) == ['id']
    assert names_of(ModelWithForeignKey.get_fk_properties()) == ['other_id']


def test_foreign_key__required(daos: TestDAOFactory):
    dao = daos[ModelWithForeignKey]
    entry = dao.create_with(id=1, insert=False)
    with pytest.raises(IntegrityError):
        dao.insert(entry)


def test_foreign_key__optional(daos: TestDAOFactory):
    dao = daos[ModelWithOptionalFk]
    dao.create_with(id=1)
    assert dao.get(1).other_id is None


def test_primary_foreign_key():
    assert TestModel.get_pk_names() == ['id']
    assert names_of(ModelWithForeignKey.get_fks()) == ['id']
    assert names_of(ModelWithForeignKey.get_fk_properties()) == ['other_id']


def test_primary_foreign_key__required(daos: TestDAOFactory):
    dao = daos[ModelWithPrimaryForeignKey]
    entry = dao.create_with(insert=False)
    with pytest.raises(IntegrityError):
        dao.insert(entry)


def test_primary_foreign_key__optional(daos: TestDAOFactory):
    dao = daos[ModelWithOptionalFk]
    dao.create_with(id=1)
    assert dao.get(1).other_id is None


def test_foreign_key__cascade_on_update(daos: TestDAOFactory):
    test_dao = daos[TestModel]
    fk_dao = daos[ModelWithForeignKey]
    optional_fk_dao = daos[ModelWithOptionalFk]

    test_entry = test_dao.create('A')
    fk_entry = fk_dao.create_with(id=1, other_id='A')
    optional_fk_entry = optional_fk_dao.create_with(id=2, other_id='A')

    test_dao.rename(test_entry, 'B')
    assert fk_entry.other_id == 'B'
    assert optional_fk_entry.other_id == 'B'


def test_foreign_key__cascade_on_delete(daos: TestDAOFactory):
    test_dao = daos[TestModel]
    fk_dao = daos[ModelWithForeignKey]

    test_entry = test_dao.create('A')
    fk_entry = fk_dao.create_with(id=1, other_id='A')
    assert fk_dao.exists(fk_entry)

    test_dao.remove(test_entry)
    assert not fk_dao.exists(fk_entry)


def test_foreign_key__on_delete_of_optional(daos: TestDAOFactory):
    test_dao = daos[TestModel]
    fk_dao = daos[ModelWithOptionalFk]

    test_entry = test_dao.create('A')
    fk_entry = fk_dao.create_with(id=1, other_id='A')
    assert fk_dao.exists(fk_entry)

    test_dao.remove(test_entry)
    assert fk_dao.exists(fk_entry)
    assert fk_entry.other_id is None


def test_foreign_key__custom_on_delete(daos: TestDAOFactory):
    test_dao = daos[TestModel]
    fk_dao = daos[ModelWithCustomOnDelete]

    test_entry = test_dao.create('A')
    fk_dao.create_with(id=1, other_id='A')

    with pytest.raises(IntegrityError):
        test_dao.remove(test_entry)
