from datetime import datetime, timezone
from typing import Optional

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field

from daomodel import DAOModel, names_of
from daomodel.fields import Identifier, utc_now, CurrentTimestampField, AutoUpdatingTimestampField, JSONField
from tests.conftest import TestDAOFactory
from tests.labeled_tests import labeled_tests


ZERO_TIMESTAMP = datetime(1970, 1, 1)


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


class ModelWithTimestamps(DAOModel, table=True):
    id: Identifier[int]
    name: Optional[str]
    created_at: datetime = CurrentTimestampField
    updated_at: datetime = AutoUpdatingTimestampField


class ModelWithJson(DAOModel, table=True):
    id: Identifier[int]
    data: dict = JSONField


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


def test_utc_now():
    now = utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo is timezone.utc


def test_current_timestamp(daos: TestDAOFactory):
    dao = daos[ModelWithTimestamps]
    dao.create(1)
    entry = dao.get(1)
    assert entry.created_at is not None
    assert entry.created_at > ZERO_TIMESTAMP


def test_auto_updating_timestamp(daos: TestDAOFactory):
    dao = daos[ModelWithTimestamps]
    dao.create(1)
    entry = dao.get(1)
    updated_at = entry.updated_at
    assert updated_at is not None
    assert updated_at > ZERO_TIMESTAMP

    entry.name = 'Test'
    dao.commit()
    assert entry.updated_at > updated_at


@labeled_tests({
    'standard json': {'Hello': 'World!', 'Lorem': ['Ipsum', 'Dolor', 'Sit', 'Amet']},
    'empty json': {},
})
def test_json_field(json: dict):
    with TestDAOFactory() as daos:
        dao = daos[ModelWithJson]
        dao.create_with(id=1, data=json)
        assert dao.get(1).data == json
