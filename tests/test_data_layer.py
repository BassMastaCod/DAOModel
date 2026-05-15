import pytest

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from daomodel.db import DataLayer
from tests.school_models import Person


def test_data_layer():
    data_layer = DataLayer()
    with data_layer.dao_context() as daos:
        with pytest.raises(OperationalError):
            daos[Person].find(name='Fyrir')
    data_layer.init_db()
    with data_layer.dao_context() as daos:
        assert daos[Person].find(name='Eftir').total == 0


def test_data_layer__engine_and_path():
    custom_engine = create_engine('sqlite://')
    with pytest.raises(ValueError):
        DataLayer(engine=custom_engine, sqlite_path='test.db')


def test_dao_context_manages_session_lifecycle(temp_data_layer):
    with temp_data_layer.dao_context() as session_one:
        dao = session_one[Person]
        dao.create_with(name='Einúlfr', age=80)
        assert dao.find().total == 1
        dao.start_transaction()
        dao.create_with(name='Annarr', age=52)
        assert dao.find().total == 2
        with temp_data_layer.dao_context() as session_two:
            print(session_one[Person].db.in_transaction())
            print(session_two[Person].db.in_transaction())
            assert session_two[Person].find().only().name == 'Einúlfr'
        assert dao.find().total == 2
