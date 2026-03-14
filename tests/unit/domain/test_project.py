from app.domain.models.project import Project


def test_project_creation():
    p = Project(name="Test Project", classes=["A", "B"])
    assert p.name == "Test Project"
    assert len(p.classes) == 2
    assert p.commands == ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]

def test_project_remove_class():
    p = Project(name="Test", classes=["cat", "dog", "bird"])
    success = p.remove_class(1) # Remove dog
    assert success is True
    assert p.classes == ["cat", "bird"]

    # Invalid index
    success = p.remove_class(10)
    assert success is False
