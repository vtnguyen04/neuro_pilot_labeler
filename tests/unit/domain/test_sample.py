from app.domain.models.label import LabelData
from app.domain.models.sample import Sample


def test_sample_from_row():
    row = {
        "image_name": "test.jpg",
        "image_path": "/data/test.jpg",
        "project_id": 1,
        "is_labeled": 1,
        "data": '{"command": 1, "bboxes": []}'
    }
    s = Sample.from_row(row)
    assert s.filename == "test.jpg"
    assert s.project_id == 1
    assert s.is_labeled is True
    assert s.label_data.command == 1

def test_sample_update_label():
    s = Sample(filename="a.jpg", image_path="p", project_id=1)
    assert s.is_labeled is False

    new_data = LabelData(command=3)
    s.update_label(new_data)

    assert s.is_labeled is True
    assert s.label_data.command == 3

def test_sample_reset():
    s = Sample(filename="a.jpg", image_path="p", project_id=1, is_labeled=True)
    s.label_data.command = 5

    s.reset_label()
    assert s.is_labeled is False
    assert s.label_data.command == 0
