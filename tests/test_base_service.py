from datetime import date
from typing import Iterable

from daomodel.base_service import BaseService, SOURCE_VALUE, DESTINATION_VALUE
from tests.conftest import Staff, TestDAOFactory


def longest(values: Iterable[str]) -> str:
    return max(values, key=len)


def setup_staff(daos: TestDAOFactory) -> tuple[Staff, Staff]:
    dao = daos[Staff]
    ed = dao.create_with(id=1, name='Ed', hire_date=date(2023, 6, 15))
    edward = dao.create_with(id=2, name='Edward', hire_date=date(2024, 8, 20))
    return ed, edward


def test_merge(daos: TestDAOFactory):
    ed, edward = setup_staff(daos)
    BaseService(daos).merge(ed, 2, name=longest, hire_date=min)
    daos.assert_in_db(Staff, 2, name='Edward', hire_date=date(2023, 6, 15))
    daos.assert_not_in_db(Staff, 1)


def test_merge__source_destination_values(daos: TestDAOFactory):
    ed, edward = setup_staff(daos)
    BaseService(daos).merge(edward, 1, name=DESTINATION_VALUE, hire_date=SOURCE_VALUE)
    daos.assert_in_db(Staff, 1, name='Ed', hire_date=date(2024, 8, 20))
    daos.assert_not_in_db(Staff, 2)
    