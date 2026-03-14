from unittest.mock import MagicMock

import pytest

from app.domain.models.project import Project
from app.domain.services.project_service import ProjectService


@pytest.fixture
def mock_repos():
    return MagicMock(), MagicMock()


def test_get_projects(mock_repos):
    p_repo, s_repo = mock_repos
    service = ProjectService(p_repo, s_repo)

    p_repo.get_projects.return_value = [Project(name="P1"), Project(name="P2")]

    projects = service.get_projects()
    assert len(projects) == 2
    assert projects[0].name == "P1"
    p_repo.get_projects.assert_called_once()


def test_create_project(mock_repos):
    p_repo, s_repo = mock_repos
    service = ProjectService(p_repo, s_repo)

    p_repo.create_project.return_value = 123

    pid = service.create_project(name="New", classes=["A"])
    assert pid == 123
    p_repo.create_project.assert_called_once()

    # Verify the object passed to repo
    args, _ = p_repo.create_project.call_args
    project_arg = args[0]
    assert project_arg.name == "New"
    assert project_arg.classes == ["A"]


def test_delete_class_logic(mock_repos):
    p_repo, s_repo = mock_repos
    service = ProjectService(p_repo, s_repo)

    project = Project(id=1, name="Test", classes=["cat", "dog", "bird"])
    p_repo.get_project.return_value = project
    s_repo.get_raw_samples_for_project.return_value = []  # No samples to heal in this test

    res = service.delete_class(1, 1)  # Delete "dog"

    assert res["status"] == "success"
    assert res["classes"] == ["cat", "bird"]
    p_repo.update_project.assert_called_once()
