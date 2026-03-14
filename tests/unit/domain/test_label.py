from app.domain.models.label import BBox, LabelData


def test_label_data_creation_defaults():
    ld = LabelData()
    assert ld.command == 0
    assert ld.bboxes == []
    assert ld.waypoints == []

def test_label_data_heal_legacy_format():
    legacy_data = {
        "bboxes": [[0.1, 0.2, 0.3, 0.4]],
        "categories": [5],
        "command": 2
    }
    ld = LabelData.create_and_heal(legacy_data)
    assert ld.command == 2
    assert len(ld.bboxes) == 1
    assert ld.bboxes[0].category == 5
    assert ld.bboxes[0].cx == 0.1
    assert ld.bboxes[0].w == 0.3

def test_label_data_remove_class():
    ld = LabelData(
        bboxes=[
            BBox(cx=0.1, cy=0.1, w=0.1, h=0.1, category=0),
            BBox(cx=0.2, cy=0.2, w=0.1, h=0.1, category=1),
            BBox(cx=0.3, cy=0.3, w=0.1, h=0.1, category=2),
        ]
    )

    # Remove class 1
    modified = ld.remove_class(1)
    assert modified is True
    assert len(ld.bboxes) == 2
    # Class 0 stays 0
    assert ld.bboxes[0].category == 0
    # Class 2 becomes 1
    assert ld.bboxes[1].category == 1
