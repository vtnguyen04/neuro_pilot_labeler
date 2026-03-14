def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    # Handle both built frontend (HTML) and warning JSON (during dev/CI)
    text = response.text.lower()
    assert "<!doctype html>" in text or "frontend was not found" in text


def test_list_labels(client):
    response = client.get("/api/v1/labels/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_image_404(client):
    response = client.get("/api/v1/labels/image/non_existent.jpg")
    assert response.status_code == 404


def test_publish_version_error(client):
    # Should fail if name is missing or invalid
    response = client.post("/api/v1/versions/", json={"name": ""})
    assert response.status_code == 422  # Validation error
