import pytest
from unittest.mock import MagicMock
from app.domain.services.project_service import ProjectService
from app.domain.models.project import Project
from app.domain.models.sample import Sample
from app.domain.models.label import LabelData, BBox

def test_merge_projects_logic(monkeypatch):
    mock_project_repo = MagicMock()
    mock_sample_repo = MagicMock()
    service = ProjectService(mock_project_repo, mock_sample_repo)

    # Setup source projects
    p1 = Project(id=1, name="P1", classes=["car", "truck"], commands=["GO"])
    p2 = Project(id=2, name="P2", classes=["pedestrian", "car"], commands=["STOP", "GO"])
    
    def get_project(pid):
        if pid == 1: return p1
        if pid == 2: return p2
        return None
    
    mock_project_repo.get_project.side_effect = get_project
    mock_project_repo.create_project.return_value = 3

    # Setup samples for P1
    s1 = Sample(
        filename="s1.jpg", 
        image_path="p1/s1.jpg", 
        project_id=1, 
        is_labeled=True,
        label_data=LabelData(bboxes=[BBox(cx=0.5, cy=0.5, w=0.1, h=0.1, category=0)], command=0) # car (cat 0), GO (cmd 0)
    )
    
    # Setup samples for P2
    s2 = Sample(
        filename="s2.jpg", 
        image_path="p2/s2.jpg", 
        project_id=2, 
        is_labeled=True,
        label_data=LabelData(bboxes=[BBox(cx=0.1, cy=0.1, w=0.1, h=0.1, category=0)], command=0) # pedestrian (cat 0), STOP (cmd 0)
    )

    mock_sample_repo.get_all_samples.side_effect = lambda limit, project_id, **kwargs: [s1] if project_id == 1 else [s2]

    # Execute Merge
    new_id = service.merge_projects([1, 2], "Merged", "Desc")

    # Assertions
    assert new_id == 3
    # Unified classes: ["car", "truck", "pedestrian"]
    # Unified commands: ["GO", "STOP"]
    mock_project_repo.create_project.assert_called_once()
    created_project = mock_project_repo.create_project.call_args[0][0]
    assert created_project.classes == ["car", "truck", "pedestrian"]
    assert created_project.commands == ["GO", "STOP"]

    # Verify mapping and copying
    # For p1: car(0)->0, truck(1)->1, GO(0)->0
    # For p2: pedestrian(0)->2, car(1)->0, STOP(0)->1, GO(1)->0
    
    assert mock_sample_repo.copy_sample_to_project.call_count == 2
    
    # Check sample from P1 re-mapping
    # call 0: (s1.filename, new_filename, 3, class_map, command_map)
    args1 = mock_sample_repo.copy_sample_to_project.call_args_list[0][0]
    assert args1[2] == 3 # new_project_id
    assert args1[3] == {0: 0, 1: 1} # class_map for P1
    assert args1[4] == {0: 0} # command_map for P1

    # Check sample from P2 re-mapping
    args2 = mock_sample_repo.copy_sample_to_project.call_args_list[1][0]
    assert args2[3] == {0: 2, 1: 0} # class_map for P2 (pedestrian->2, car->0)
    assert args2[4] == {0: 1, 1: 0} # command_map for P2 (STOP->1, GO->0)
