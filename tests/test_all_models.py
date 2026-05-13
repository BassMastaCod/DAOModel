from sqlmodel import SQLModel

from daomodel import all_models
from daomodel.db import _create_engine
from tests.school_models import *


@pytest.mark.xfail(reason='Fails unless run individually (to better control loaded models)')
def test_all_models():
    engine = _create_engine()
    SQLModel.metadata.create_all(engine)
    expected = {Person, Book, Hall, Locker, Staff, Student}
    assert all_models(engine) == expected
    connection = engine.connect()
    assert all_models(connection) == expected
