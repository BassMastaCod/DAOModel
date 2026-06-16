from daomodel import DAOModel
from typing import Optional

from daomodel.fields import Identifier
from daomodel.util import next_id


class DefaultModel(DAOModel, table=True):
    id: Identifier[int]
    field: Optional[int] = 1


def test_default_value__omitted(daos):
    model = daos[DefaultModel].create(next_id())
    assert model.field == 1


def test_default_value__omitted__constructor(daos):
    model = DefaultModel()
    daos.db.add(model)
    daos.db.commit()
    daos.db.refresh(model)
    assert model.field == 1


def test_default_value__provided(daos):
    model = daos[DefaultModel].create_with(id=100, field=2)
    assert model.field == 2


def test_default_value__provided__constructor(daos):
    model = DefaultModel(field=2)
    daos.db.add(model)
    daos.db.commit()
    daos.db.refresh(model)
    assert model.field == 2


def test_default_value__explicitly_null(daos):
    model = daos[DefaultModel].create_with(id=100, field=None)
    assert model.field is None


def test_default_value__explicitly_null__constructor(daos):
    model = DefaultModel(field=None)
    daos.db.add(model)
    daos.db.commit()
    daos.db.refresh(model)
    assert model.field is None
