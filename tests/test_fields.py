from datetime import timezone, datetime, timedelta
from typing import Optional
from unittest.mock import Mock

import pytest
from sqlalchemy import text

from daomodel import DAOModel
from daomodel.fields import utc_now, Identifier, CurrentTimestampField, AutoUpdatingTimestampField, utc_datetime, \
    server_datetime, ServerDateTimeError, _to_server_local
from daomodel.testing import labeled_tests, Expected, TestDAOFactory
from tests.model_factory import create_test_model

D = datetime(2026, 8, 14, 12, 0)
OTHER_TZ = timezone(timedelta(hours=5, minutes=30))
LOCAL_TZ = datetime.now().astimezone().tzinfo
DATE = D
DATE_UTC = D.replace(tzinfo=timezone.utc)      # the instant as UTC
DATE_SERVER = DATE_UTC.astimezone()            # the same instant, server-local
DATE_OTHER = DATE_UTC.astimezone(OTHER_TZ)     # the same instant, +5:30


class BasicModel(DAOModel, table=True):
    id: Identifier[int]


class ExpandedModel(BasicModel, table=True):
    name: str


class InheritedModel(ExpandedModel, table=True):
    pass


class TimestampsModel(DAOModel, table=True):
    id: Identifier[int]
    name: Optional[str]
    created_at: datetime = CurrentTimestampField
    updated_at: datetime = AutoUpdatingTimestampField


class UTCTimestampsModel(DAOModel, table=True):
    id: Identifier[int]
    name: Optional[str]
    created_at: utc_datetime = CurrentTimestampField
    updated_at: utc_datetime = AutoUpdatingTimestampField


class ServerTimestampsModel(DAOModel, table=True):
    id: Identifier[int]
    name: Optional[str]
    created_at: server_datetime = CurrentTimestampField
    updated_at: server_datetime = AutoUpdatingTimestampField


def test_utc_now():
    now = utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo is timezone.utc


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


TIMESTAMP_MODELS = {
    'datetime': [TimestampsModel],
    'utc_datetime': [UTCTimestampsModel],
    'server_datetime': [ServerTimestampsModel],
}


@labeled_tests(TIMESTAMP_MODELS)
def test_current_timestamp(model):
    with TestDAOFactory() as daos:
        dao = daos[model]
        before = utc_now()
        dao.create(1)
        entry = dao.get(1)
        assert entry.created_at is not None
        assert before <= _to_utc(entry.created_at) <= utc_now()


@labeled_tests(TIMESTAMP_MODELS)
def test_auto_updating_timestamp(model):
    with TestDAOFactory() as daos:
        dao = daos[model]
        before = utc_now()
        dao.create(1)
        entry = dao.get(1)
        assert entry.updated_at is not None
        assert before <= _to_utc(entry.updated_at) <= utc_now()

        entry.name = 'Test'
        before = utc_now()
        dao.commit()
        assert before <= _to_utc(entry.updated_at) <= utc_now()


@labeled_tests({
    'no_timezone': [
        Expected(None),
        (datetime, DATE),
        (datetime, DATE_UTC),
        (datetime, DATE_SERVER),
        (datetime, DATE_OTHER),
    ],
    'utc': [
        Expected(timezone.utc),
        (utc_datetime, DATE),
        (utc_datetime, DATE_UTC),
        (utc_datetime, DATE_SERVER),
        (utc_datetime, DATE_OTHER),
    ],
    'local': [
        Expected(LOCAL_TZ),
        (server_datetime, DATE),
        (server_datetime, DATE_UTC),
        (server_datetime, DATE_SERVER),
        (server_datetime, DATE_OTHER),
    ],
})
def test_datetime_loading(field_type, value, expected_tz):
    model = create_test_model(field_type)
    with TestDAOFactory() as daos:
        daos[model].create_with(id=1, value=value)
        loaded = daos[model].get(1).value
        assert loaded.tzinfo == expected_tz


@labeled_tests({
    'datetime': [
        (datetime, DATE, DATE_UTC),
        (datetime, DATE_UTC, DATE_UTC),
        (datetime, DATE_SERVER, DATE_SERVER),
        (datetime, DATE_OTHER, DATE_OTHER),
    ],
    'utc_datetime': [
        Expected(DATE_UTC),
        (utc_datetime, DATE),
        (utc_datetime, DATE_UTC),
        (utc_datetime, DATE_SERVER),
        (utc_datetime, DATE_OTHER),
    ],
    'server_datetime': [
        Expected(DATE_SERVER),
        (server_datetime, DATE_UTC),
        (server_datetime, DATE_SERVER),
        (server_datetime, DATE_OTHER),
    ],
})
def test_datetime_storing(field_type, value, expected):
    model = create_test_model(field_type)
    with TestDAOFactory() as daos:
        daos[model].create_with(id=1, value=value)
        with daos.session_factory() as session:
            raw = session.execute(text(f'SELECT value FROM {model.__tablename__}')).scalar_one()
            assert datetime.fromisoformat(raw).replace(tzinfo=None) == expected.replace(tzinfo=None)


def test_server_datetime_treats_naive_as_server_local():
    model = create_test_model(server_datetime)
    with TestDAOFactory() as daos:
        daos[model].create_with(id=1, value=DATE)
        loaded = daos[model].get(1).value.replace(tzinfo=None)
        assert loaded == DATE


def test_server_datetime_error_message():
    err = ServerDateTimeError(datetime(1900, 1, 1, tzinfo=timezone.utc))
    assert 'server-local time' in err.detail
    assert 'utc_datetime' in err.detail


def test_to_server_local_raises_clear_error_on_unrepresentable():
    value = Mock(astimezone=Mock(side_effect=OSError))
    with pytest.raises(ServerDateTimeError):
        _to_server_local(value)
