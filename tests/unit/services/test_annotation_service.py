from unittest.mock import MagicMock

import pytest

from app.domain.models.sample import Sample
from app.domain.services.annotation_service import AnnotationService
from app.schemas.label import LabelUpdate


@pytest.fixture
def mock_repos():
    return MagicMock(), MagicMock()


def test_get_sample_detail(mock_repos):
    s_repo, p_repo = mock_repos
    service = AnnotationService(s_repo, p_repo)

    sample = Sample(filename="test.jpg", image_path="p", project_id=1)
    sample.label_data.command = 3
    s_repo.get_sample.return_value = sample

    res = service.get_sample_detail("test.jpg")
    assert res["filename"] == "test.jpg"
    assert res["command"] == 3


def test_update_label(mock_repos):
    s_repo, p_repo = mock_repos
    service = AnnotationService(s_repo, p_repo)

    sample = Sample(filename="update.jpg", image_path="p", project_id=1)
    s_repo.get_sample.return_value = sample

    update = LabelUpdate(command=2, bboxes=[], waypoints=[])

    res = service.update_label("update.jpg", update)

    assert res["status"] == "success"
    assert sample.label_data.command == 2
    assert sample.is_labeled is True
    s_repo.save_label.assert_called_once()
