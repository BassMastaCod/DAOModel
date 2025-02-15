import pytest

from daomodel import all_models
from daomodel.db import create_engine, init_db
from tests.conftest import Person, Book, Hall, Locker, Staff, Student


@pytest.mark.xfail(reason='Fails unless run individually (to better control loaded models)')
def test_all_models():
    engine = create_engine()
    init_db(engine)
    assert all_models(engine) == {Person, Book, Hall, Locker, Staff, Student}
