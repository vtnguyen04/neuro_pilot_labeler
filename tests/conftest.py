import os
import tempfile
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.label_router import get_db_path, get_storage_provider


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
def mock_storage():
    mock = MagicMock()
    # Default behavior: resolve_file_path returns None (not found)
    mock.resolve_file_path.return_value = None
    return mock


@pytest.fixture
def client(test_db, mock_storage):
    def override_get_db_path():
        return test_db

    def override_get_storage_provider():
        return mock_storage

    app.dependency_overrides[get_db_path] = override_get_db_path
    app.dependency_overrides[get_storage_provider] = override_get_storage_provider
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
