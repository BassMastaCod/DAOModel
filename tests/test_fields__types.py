from typing import Optional, Any
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field

from daomodel import DAOModel
from daomodel.fields import Protected, Identifier
from tests.conftest import TestDAOFactory
from tests.labeled_tests import labeled_tests
from tests.model_factory import create_test_model
from tests.test_fields import BasicModel
from tests.test_fields__inherited import get_test_cases


class OtherModel(DAOModel, table=True):
    id: Identifier[str]


class StandardReferenceModel(DAOModel, table=True):
    id: Identifier[int]
    other_id: OtherModel


class OptionalReferenceModel(DAOModel, table=True):
    id: Identifier[int]
    other_id: Optional[OtherModel]


class RestrictModel(DAOModel, table=True):
    id: Identifier[int]
    other_id: Protected[OtherModel]


class CustomOnDeleteModel(DAOModel, table=True):
    id: Identifier[int]
    other_id: Optional[OtherModel] = Field(foreign_key='auto', ondelete='CASCADE')


class UUIDModel(DAOModel, table=True):
    id: Identifier[UUID]


class UUIDReferenceModel(DAOModel, table=True):
    id: Identifier[int]
    other_id: UUIDModel


class UUIDOptionalReferenceModel(DAOModel, table=True):
    id: Identifier[int]
    other_id: Optional[UUIDModel]


@labeled_tests({**get_test_cases('field')})
def test_field(annotation: Any):
    model_type = create_test_model(annotation)
    with TestDAOFactory() as daos:
        dao = daos[model_type]
        dao.create_with(id=1, value='test')
        entry = dao.find(id=1)
        assert entry.only().value == 'test'


@labeled_tests(get_test_cases('uuid'))
def test_uuid(annotation: Any):
    model_type = create_test_model(annotation)
    with TestDAOFactory() as daos:
        dao = daos[model_type]
        entry = dao.create_with(id=1)

        assert getattr(entry, 'value') is not None
        assert isinstance(getattr(entry, 'value'), UUID)

        entry2 = dao.create_with(id=2)
        assert getattr(entry2, 'value') is not None
        assert isinstance(getattr(entry2, 'value'), UUID)
        assert getattr(entry, 'value') != getattr(entry2, 'value')


@labeled_tests(get_test_cases('dict'))
def test_dict(annotation: Any):
    model_type = create_test_model(annotation)
    sample_dict = {'Hello': 'World!', 'Lorem': ['Ipsum', 'Dolor', 'Sit', 'Amet']}
    with TestDAOFactory() as daos:
        daos[model_type].create_with(id=1, value=sample_dict)
        daos.assert_in_db(model_type, 1, value=sample_dict)


@labeled_tests(get_test_cases('reference'))
def test_reference(annotation: Any):
    model_type = create_test_model(annotation)
    with TestDAOFactory() as daos:
        daos[BasicModel].create(100)
        dao = daos[model_type]
        dao.create_with(id=1, value=100)
        entry = dao.find(id=1)
        assert entry.only().value == 100


def test_reference__cascade_on_update(daos: TestDAOFactory):
    test_dao = daos[OtherModel]
    fk_dao = daos[StandardReferenceModel]
    optional_fk_dao = daos[OptionalReferenceModel]

    other_entry = test_dao.create('A')
    fk_entry = fk_dao.create_with(id=1, other_id='A')
    optional_fk_entry = optional_fk_dao.create_with(id=2, other_id='A')

    test_dao.rename(other_entry, 'B')
    assert fk_entry.other_id == 'B'
    assert optional_fk_entry.other_id == 'B'


def test_reference__cascade_on_delete(daos: TestDAOFactory):
    test_dao = daos[OtherModel]
    fk_dao = daos[StandardReferenceModel]

    other_entry = test_dao.create('A')
    fk_dao.create_with(id=1, other_id='A')
    daos.assert_in_db(StandardReferenceModel, 1, other_id='A')

    test_dao.remove(other_entry)
    daos.assert_not_in_db(StandardReferenceModel, 1)


def test_reference__on_delete_of_optional(daos: TestDAOFactory):
    test_dao = daos[OtherModel]
    fk_dao = daos[OptionalReferenceModel]

    other_entry = test_dao.create('A')
    fk_dao.create_with(id=1, other_id='A')
    daos.assert_in_db(OptionalReferenceModel, 1, other_id='A')

    test_dao.remove(other_entry)
    daos.assert_in_db(OptionalReferenceModel, 1, other_id=None)


def test_reference__override_on_delete(daos: TestDAOFactory):
    test_dao = daos[OtherModel]
    fk_dao = daos[CustomOnDeleteModel]

    fk_entry = fk_dao.create(1)
    daos.assert_in_db(CustomOnDeleteModel, 1, other_id=None)

    other_entry = test_dao.create('A')
    fk_entry.other_id = other_entry.id
    fk_dao.upsert(fk_entry)
    daos.assert_in_db(CustomOnDeleteModel, 1, other_id='A')

    test_dao.remove(other_entry)
    daos.assert_not_in_db(CustomOnDeleteModel, 1)


def test_reference__protected(daos: TestDAOFactory):
    test_dao = daos[OtherModel]
    fk_dao = daos[RestrictModel]

    other_entry = test_dao.create('A')
    fk_dao.create_with(id=1, other_id='A')

    with pytest.raises(IntegrityError):
        test_dao.remove(other_entry)


def test_reference__uuid(daos: TestDAOFactory):
    uuid_dao = daos[UUIDModel]
    reference_dao = daos[UUIDReferenceModel]

    uuid_model = daos[UUIDModel].create_with()
    reference_dao.create_with(id=1, other_id=uuid_model.id)

    entry = reference_dao.get(1)
    assert entry.other_id is not None
    assert uuid_dao.get(entry.other_id) is not None


def test_reference__uuid__optional(daos: TestDAOFactory):
    daos[UUIDOptionalReferenceModel].create(1)
    daos.assert_in_db(UUIDOptionalReferenceModel, 1, other_id=None)
