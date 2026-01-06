from datetime import datetime

import pytest

from daomodel import DAOModel
from daomodel.dao import DAO
from daomodel.fields import Identifier
from daomodel.search_util import Equals, NotEquals, AnyOf, NoneOf, Before, After, Between, And, Or, ConditionOperator
from daomodel.testing import TestDAOFactory


class Flight(DAOModel, table=True):
    id: Identifier[str]
    origin: str
    dest: str
    dep: datetime


@pytest.fixture
def flight_dao(daos: TestDAOFactory) -> DAO:
    dao = daos[Flight]
    dao.create_with(id='AA101', origin='NYC', dest='CHI', dep=datetime(2023, 1, 15, 8, 30))
    dao.create_with(id='DL202', origin='ATL', dest='BOS', dep=datetime(2023, 6, 20, 22, 15))
    dao.create_with(id='UA303', origin='DEN', dest='SFO', dep=datetime(2024, 3, 5, 14, 45))
    dao.create_with(id='SW404', origin='DAL', dest='MCO', dep=datetime(2024, 12, 25, 6, 0))
    dao.create_with(id='JB505', origin='MIA', dest='NYC', dep=datetime(2025, 7, 4, 11, 10))
    dao.create_with(id='AA606', origin='CHI', dest='LAX', dep=datetime(2025, 12, 9, 7, 0))
    dao.create_with(id='DL707', origin='SEA', dest='ATL', dep=datetime(2026, 2, 14, 13, 15))
    dao.create_with(id='UA808', origin='HOU', dest='DEN', dep=datetime(2026, 8, 30, 17, 45))
    dao.create_with(id='SW909', origin='PHX', dest='LAS', dep=datetime(2027, 5, 10, 10, 0))
    dao.create_with(id='JB010', origin='BOS', dest='WAS', dep=datetime(2027, 11, 1, 16, 30))
    dao.create_with(id='AA111', origin='NYC', dest='LON', dep=datetime(2028, 4, 18, 23, 55))
    dao.create_with(id='DL212', origin='ATL', dest='PAR', dep=datetime(2028, 9, 9, 5, 45))
    return dao


@pytest.mark.parametrize('operator, expected', [
    (Equals(2026, _part='year'), {'DL707', 'UA808'}),
    (NotEquals(12, _part='month'), {'AA101', 'DL202', 'UA303', 'JB505', 'DL707', 'UA808', 'SW909', 'JB010', 'AA111', 'DL212'}),
    (AnyOf(10, 12, 14, _part='day'), {'DL707', 'SW909'}),
    (NoneOf(0, 15, 30, 45, _part='minute'), {'JB505', 'AA111'}),
    (Before(2025, _part='year'), {'AA101', 'DL202', 'UA303', 'SW404'}),
    (After(14, _part='hour'), {'DL202', 'UA808', 'JB010', 'AA111'}),
    (Between(6, 10, _part='hour'), {'AA101', 'SW404', 'AA606', 'SW909'}),
    (And(Equals(12, _part='month'), After(20, _part='day')), {'SW404'}),
    (Or(Before(9, _part='hour'), After(17, _part='hour')), {'AA101', 'DL202', 'SW404', 'AA606', 'AA111', 'DL212'}),
    (Or(And(Equals(12, _part='month'), Equals(25, _part='day')), And(Equals(1, _part='month'), Equals(1, _part='day'))), {'SW404'})
])
def test_find__by_part(flight_dao, operator: ConditionOperator, expected: set[str]):
    assert {flight.id for flight in flight_dao.find(dep=operator)} == expected
