from datetime import date

import pytest

from daomodel.base_service import SingleModelService, SOURCE_VALUE, DESTINATION_VALUE, BaseService
from tests.conftest import TestDAOFactory
from tests.school_models import Staff, Student


def longest(values: list[str]) -> str:
    return max(values, key=len)


def setup_staff(daos: TestDAOFactory) -> tuple[Staff, Staff]:
    dao = daos[Staff]
    ed = dao.create_with(id=1, name='Ed', hire_date=date(2023, 6, 15))
    edward = dao.create_with(id=2, name='Edward', hire_date=date(2024, 8, 20))
    return ed, edward


def test_merge(daos: TestDAOFactory):
    ed, edward = setup_staff(daos)
    SingleModelService(daos, Staff).merge(ed, 2, name=longest, hire_date=min)
    daos.assert_in_db(Staff, 2, name='Edward', hire_date=date(2023, 6, 15))
    daos.assert_not_in_db(Staff, 1)


def test_merge__source_destination_values(daos: TestDAOFactory):
    ed, edward = setup_staff(daos)
    service = SingleModelService(daos, Staff)
    service.merge(edward, 1, name=DESTINATION_VALUE, hire_date=SOURCE_VALUE)
    daos.assert_in_db(Staff, 1, name='Ed', hire_date=date(2024, 8, 20))
    daos.assert_not_in_db(Staff, 2)


def test_merge__mismatched_model_type(daos: TestDAOFactory):
    setup_staff(daos)
    service = SingleModelService(daos, Staff)
    student = daos[Student].create_with(id=100, name='Student', gender='m')

    with pytest.raises(TypeError):
        service.merge(student, 1)


def test_dao(daos: TestDAOFactory):
    service = SingleModelService(daos, Staff)
    staff = service.dao.create_with(id=3, name='Alice', hire_date=date(2023, 1, 15))

    daos.assert_in_db(Staff, 3, name='Alice', hire_date=date(2023, 1, 15))

    staff.name = 'Alicia'
    service.dao.commit(staff)

    daos.assert_in_db(Staff, 3, name='Alicia', hire_date=date(2023, 1, 15))


def test_bulk_update(daos: TestDAOFactory):
    # Create multiple staff members
    dao = daos[Staff]
    staff1 = dao.create_with(id=10, name='Staff1', hire_date=date(2023, 1, 15))
    staff2 = dao.create_with(id=11, name='Staff2', hire_date=date(2023, 2, 20))
    staff3 = dao.create_with(id=12, name='Staff3', hire_date=date(2023, 3, 25))

    # Update all staff members with the same values
    service = SingleModelService(daos, Staff)
    service.bulk_update([staff1, staff2, staff3], hire_date=date(2024, 1, 1))

    # Verify all staff members were updated
    daos.assert_in_db(Staff, 10, name='Staff1', hire_date=date(2024, 1, 1))
    daos.assert_in_db(Staff, 11, name='Staff2', hire_date=date(2024, 1, 1))
    daos.assert_in_db(Staff, 12, name='Staff3', hire_date=date(2024, 1, 1))


def test_bulk_update__no_model_class(daos: TestDAOFactory):
    # Create multiple staff members
    dao = daos[Staff]
    staff1 = dao.create_with(id=20, name='Staff1', hire_date=date(2023, 1, 15))
    staff2 = dao.create_with(id=21, name='Staff2', hire_date=date(2023, 2, 20))

    # Update staff members without specifying model_class
    service = BaseService(daos)
    service.bulk_update([staff1, staff2], name='Updated Staff')

    # Verify all staff members were updated
    daos.assert_in_db(Staff, 20, name='Updated Staff', hire_date=date(2023, 1, 15))
    daos.assert_in_db(Staff, 21, name='Updated Staff', hire_date=date(2023, 2, 20))


def test_bulk_update__empty_list(daos: TestDAOFactory):
    # Should not raise an error when the list is empty
    service = SingleModelService(daos, Staff)
    service.bulk_update([], name='Should not be applied')


def test_bulk_update__mixed_model_types(daos: TestDAOFactory):
    # Create staff and student
    staff = daos[Staff].create_with(id=30, name='Staff', hire_date=date(2023, 1, 15))
    student = daos[Student].create_with(id=200, name='Student', gender='m')

    # Update models of different types
    service = BaseService(daos)
    service.bulk_update([staff, student], name='Updated Name')

    # Verify both models were updated
    daos.assert_in_db(Staff, 30, name='Updated Name', hire_date=date(2023, 1, 15))
    daos.assert_in_db(Student, 200, name='Updated Name', gender='m')


def test_bulk_update__multiple_mixed_models(daos: TestDAOFactory):
    # Create multiple staff and student models
    staff_dao = daos[Staff]
    student_dao = daos[Student]

    staff1 = staff_dao.create_with(id=40, name='Staff1', hire_date=date(2023, 1, 15))
    staff2 = staff_dao.create_with(id=41, name='Staff2', hire_date=date(2023, 2, 20))
    student1 = student_dao.create_with(id=300, name='Student1', gender='m')
    student2 = student_dao.create_with(id=301, name='Student2', gender='f')

    # Mix the models in a single list
    mixed_models = [staff1, student1, staff2, student2]

    # Update all models with a common field they inherit from BasePerson
    service = BaseService(daos)
    service.bulk_update(mixed_models, name='Common Name')

    # Verify all models were updated correctly
    daos.assert_in_db(Staff, 40, name='Common Name', hire_date=date(2023, 1, 15))
    daos.assert_in_db(Staff, 41, name='Common Name', hire_date=date(2023, 2, 20))
    daos.assert_in_db(Student, 300, name='Common Name', gender='m')
    daos.assert_in_db(Student, 301, name='Common Name', gender='f')
