def test_project_lifecycle(client):
    # 1. Create Project
    response = client.post("/api/v1/labels/projects", json={
        "name": "Integration Test Project",
        "classes": ["Car", "Person"],
        "commands": ["FOLLOW", "STOP"]
    })
    assert response.status_code == 200
    project_id = response.json()
    assert isinstance(project_id, int)

    # 2. Get Project
    response = client.get("/api/v1/labels/projects")
    assert response.status_code == 200
    projects = response.json()
    assert any(p["id"] == project_id for p in projects)

    # 3. Update Classes
    response = client.post(f"/api/v1/labels/projects/{project_id}/classes", json=["Car", "Person", "Bike"])
    assert response.status_code == 200

    response = client.get(f"/api/v1/labels/projects/{project_id}/classes")
    assert response.json() == ["Car", "Person", "Bike"]

def test_list_labels_empty(client):
    response = client.get("/api/v1/labels/")
    assert response.status_code == 200
    assert response.json() == []
