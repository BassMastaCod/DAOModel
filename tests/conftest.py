from typing import Any, Generator

import pytest

from daomodel.testing import TestDAOFactory


@pytest.fixture(name='daos')
def daos_fixture() -> Generator[TestDAOFactory, Any, None]:
    """
    Provides a DAOFactory for Testing as a pytest fixture named `daos`.

    Change to `TestDAOFactory(debug=True)` in order to write the DB to file.
    NOTE: this avoids cleaning up test data after test execution, allowing for inspection
        As a result will, subsequent tests will likely fail due to not having a clean DB.
    """
    with TestDAOFactory() as daos:
        yield daos
