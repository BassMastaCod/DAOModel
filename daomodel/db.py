from contextlib import contextmanager
from typing import Optional

import sqlalchemy
from sqlalchemy import Engine, event
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from daomodel import DAOModel
from daomodel.dao import DAO
from daomodel.transaction import TransactionMixin


def _create_engine(path: Optional[str] = None) -> Engine:
    """Creates an SQLite Engine.

    see DataLayer

    :param path: the path to the DB file or None to keep the DB in-memory
    :return: The newly created SQLite Engine
    """
    @event.listens_for(Engine, 'connect')
    def enforce_fk_constraints_for_sqlite(connection, _connection_record) -> None:
        cursor = connection.cursor()
        cursor.execute('pragma foreign_keys=on')
        cursor.close()

    if path is None:
        path = ''
        pool = sqlalchemy.StaticPool
    else:
        path = '/' + path
        pool = None
    return sqlalchemy.create_engine(
        'sqlite://' + path,
        connect_args={'check_same_thread': False},
        poolclass=pool
    )


class DAOFactory(TransactionMixin):
    """A Factory for creating DAOs for DAOModels.

    Usage:
        # Create a DAOFactory with a session_factory
        # Use a `with` statement to auto-close all DAOs/Sessions afterwards
        with DAOFactory(sessionmaker(bind=engine)) as daos:
            # Get a DAO for a specific DAOModel
            dao = daos[MyModelType]

    see DataLayer
    """
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def __enter__(self) -> 'DAOFactory':
        self.db = self.session_factory()
        return self

    def __getitem__(self, model: type[DAOModel]) -> DAO:
        return DAO(model, self.db)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.db.close()


class DataLayer:
    def __init__(self, engine: Optional[Engine] = None, sqlite_path: Optional[str] = None):
        if engine and sqlite_path:
            raise ValueError('Cannot specify both engine and SQLite path. Please choose one or the other.')
        self.engine = engine or _create_engine(sqlite_path)
        self.sessionmaker = sessionmaker(bind=self.engine)

    def init_db(self) -> None:
        """Initiates DB tables of all imported SQL/DAOModels

        Calling this too early will result in tables missing from your DB.
        """
        SQLModel.metadata.create_all(self.engine)

    @contextmanager
    def dao_context(self):
        with DAOFactory(self.sessionmaker) as daos:
            yield daos
