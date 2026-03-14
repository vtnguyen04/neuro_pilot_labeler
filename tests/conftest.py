import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.label_router import get_db_path


@pytest.fixture(scope="session")
def test_db():
    fd, path = tempfile.mkstemp()
    try:
        yield path
    finally:
        os.close(fd)
        if os.path.exists(path):
            os.unlink(path)

@pytest.fixture
def client(test_db):
    def override_get_db_path():
        return test_db

    app.dependency_overrides[get_db_path] = override_get_db_path
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
