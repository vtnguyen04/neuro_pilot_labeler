import pytest
from unittest.mock import MagicMock
from app.repositories.sample_repository import SampleRepository
import sqlite3

def test_filter_has_control_points_logic(tmp_path):
    db_path = str(tmp_path / "test.db")
    from app.repositories.project_repository import ProjectRepository
    ProjectRepository(db_path)._init_db()
    repo = SampleRepository(db_path)
    repo._init_db()
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (1, 'Test Project')")
        
        # Sample with control points
        conn.execute("INSERT INTO samples (image_name, image_path, project_id, data, is_labeled) VALUES (?, ?, ?, ?, ?)",
                    ("has_cp.jpg", "p1.jpg", 1, '{"control_points": [{"x":0.1, "y":0.1}, {"x":0.2, "y":0.2}]}', 1))
        
        # Sample with empty control points
        conn.execute("INSERT INTO samples (image_name, image_path, project_id, data, is_labeled) VALUES (?, ?, ?, ?, ?)",
                    ("empty_cp.jpg", "p2.jpg", 1, '{"control_points": []}', 1))
        
        # Sample without control_points field
        conn.execute("INSERT INTO samples (image_name, image_path, project_id, data, is_labeled) VALUES (?, ?, ?, ?, ?)",
                    ("no_cp_field.jpg", "p3.jpg", 1, '{"bboxes": []}', 1))
        
        # Sample with null control_points
        conn.execute("INSERT INTO samples (image_name, image_path, project_id, data, is_labeled) VALUES (?, ?, ?, ?, ?)",
                    ("null_cp.jpg", "p4.jpg", 1, '{"control_points": null}', 1))
        
        conn.commit()

    # Test Filter HAS CP
    res = repo.get_all_samples(project_id=1, has_control_points=True)
    assert len(res) == 1
    assert res[0].filename == "has_cp.jpg"

    # Test Filter NO CP (should catch empty, missing, and null)
    res = repo.get_all_samples(project_id=1, has_control_points=False)
    assert len(res) == 3
    filenames = [s.filename for s in res]
    assert "empty_cp.jpg" in filenames
    assert "no_cp_field.jpg" in filenames
    assert "null_cp.jpg" in filenames
