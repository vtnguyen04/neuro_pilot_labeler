from unittest.mock import MagicMock

import pytest

from app.domain.models.sample import Sample
from app.domain.services.sample_service import SampleService


@pytest.fixture
def mock_repo():
    return MagicMock()


def test_get_samples_mapping(mock_repo):
    service = SampleService(mock_repo)

    mock_repo.get_all_samples.return_value = [Sample(filename="1.jpg", image_path="p1", project_id=1, is_labeled=True)]

    result = service.get_samples()
    assert len(result) == 1
    assert result[0]["filename"] == "1.jpg"
    assert result[0]["is_labeled"] is True
    # Verify flattening or data presence
    assert "command" in result[0]


def test_delete_sample_flow(mock_repo):
    service = SampleService(mock_repo)

    sample = Sample(filename="del.jpg", image_path="path/to/img.jpg", project_id=1)
    mock_repo.get_sample.return_value = sample
    mock_repo.count_references_to_path.return_value = 1  # Still referenced by someone else

    res = service.delete_sample("del.jpg")

    assert res["status"] == "deleted"
    assert res["physical_file_removed"] is False
    mock_repo.delete_sample.assert_called_once_with("del.jpg")
