import pytest
from fastapi.testclient import TestClient
from app.main import app
import sqlite3
from app.core.config import Config

client = TestClient(app)

def test_merge_projects_api(monkeypatch, tmp_path):
    # Mock DB path
    db_path = str(tmp_path / "test_api.db")
    monkeypatch.setattr(Config, "DB_PATH", db_path)
    
    # Initialize DB
    from app.repositories.project_repository import ProjectRepository
    from app.repositories.sample_repository import SampleRepository
    ProjectRepository(db_path)._init_db()
    SampleRepository(db_path)._init_db()

    # 1. Create two projects
    p1_res = client.post("/api/v1/labels/projects", json={"name": "P1", "classes": ["c1"]})
    p1_id = p1_res.json()
    p2_res = client.post("/api/v1/labels/projects", json={"name": "P2", "classes": ["c2"]})
    p2_id = p2_res.json()

    # 2. Add a sample to P1
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO samples (image_name, image_path, project_id, data, is_labeled) VALUES (?, ?, ?, ?, ?)",
                    ("s1.jpg", "path/s1.jpg", p1_id, '{"bboxes": [{"category": 0, "cx":0.5, "cy":0.5, "w":0.1, "h":0.1}], "command": 0}', 1))
        conn.commit()

    # 3. Call Merge API
    merge_res = client.post("/api/v1/labels/projects/merge", json={
        "project_ids": [p1_id, p2_id],
        "new_name": "Merged Project"
    })
    
    assert merge_res.status_code == 200
    data = merge_res.json()
    assert data["status"] == "success"
    new_project_id = data["new_project_id"]

    # 4. Verify new project exists and has merged classes
    proj_res = client.get("/api/v1/labels/projects")
    projects = proj_res.json()
    merged_proj = next(p for p in projects if p["id"] == new_project_id)
    assert "c1" in merged_proj["classes"]
    assert "c2" in merged_proj["classes"]

    # 5. Verify sample was copied and re-mapped
    samples_res = client.get(f"/api/v1/labels/?project_id={new_project_id}")
    samples = samples_res.json()
    assert len(samples) == 1
    assert samples[0]["filename"] == f"merged_{p1_id}_s1.jpg"
