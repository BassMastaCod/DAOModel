from typing import Any, Generator

import pytest
from _pytest.outcomes import fail
from sqlalchemy.orm import sessionmaker

from daomodel import DAOModel
from daomodel.dao import NotFound, DAO
from daomodel.db import DAOFactory, create_engine, init_db


class TestDAOFactory(DAOFactory):
    """
    A DAOFactory specifically designed for pytest.
    Includes functionality that can assert what is committed within the DB (through a secondary Session).
    """
    def __init__(self):
        engine = create_engine()  # create_engine('test.db')  # See DB for debugging, must delete file to rerun
        init_db(engine)
        super().__init__(sessionmaker(bind=engine))

    def __enter__(self) -> 'TestDAOFactory':
        super().__enter__()
        return self

    def assert_in_db(self, model: type[DAOModel], *pk, **expected_values: Any) -> None:
        """
        Assert that an object with specific attribute values is present in the DB.
        This checks the committed state of the database, not the session state.

        :param model: The DB table to check
        :param pk: The primary key values of the row
        :param expected_values: The column values to assert
        """
        with self.session_factory() as fresh_session:
            try:
                persisted_copy = DAO(model, fresh_session).get(*pk)
                for key, expected in expected_values.items():
                    actual = getattr(persisted_copy, key)
                    assert actual == expected, f'expected {key} of {persisted_copy} to be {expected} but was {actual}'
            except NotFound as e:
                fail(e.detail)

    def assert_not_in_db(self, model: type[DAOModel], *pk: Any) -> None:
        """
        Assert that the specified object is not present in the DB.
        This checks the committed state of the database, not the session state.

        :param model: The DB table to check
        :param pk: The primary key values of the row
        """
        with self.session_factory() as fresh_session:
            with pytest.raises(NotFound):
                DAO(model, fresh_session).get(*pk)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)


@pytest.fixture(name='daos')
def daos_fixture() -> Generator[TestDAOFactory, Any, None]:
    """
    Provides a DAOFactory for Testing as a pytest fixture named `daos`.
    """
    with TestDAOFactory() as daos:
        yield daos
