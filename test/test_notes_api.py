def test_list_notes_empty(client):
    response = client.get("/api/notes")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_and_list_note(client):
    response = client.post("/api/notes", json={"title": "First", "content": "Hello"})

    assert response.status_code == 201
    created = response.get_json()
    assert created["title"] == "First"
    assert created["content"] == "Hello"
    assert isinstance(created["id"], str)

    listing = client.get("/api/notes").get_json()
    assert [note["id"] for note in listing] == [created["id"]]


def test_update_note(client):
    created = client.post(
        "/api/notes", json={"title": "Original", "content": "Original content"}
    ).get_json()

    response = client.put(
        f"/api/notes/{created['id']}",
        json={"title": "Updated", "content": "New content"},
    )

    assert response.status_code == 200
    updated = response.get_json()
    assert updated["id"] == created["id"]
    assert updated["title"] == "Updated"
    assert updated["content"] == "New content"
    assert updated["created_at"] == created["created_at"]
    assert updated["updated_at"] > created["updated_at"]

    listing = client.get("/api/notes").get_json()
    assert listing[0]["title"] == "Updated"


def test_delete_note(client):
    created = client.post(
        "/api/notes", json={"title": "Delete me", "content": "Temporary"}
    ).get_json()

    response = client.delete(f"/api/notes/{created['id']}")

    assert response.status_code == 204
    assert response.data == b""
    assert client.get("/api/notes").get_json() == []


def test_missing_note_returns_404(client):
    update_response = client.put(
        "/api/notes/missing", json={"title": "Title", "content": "Content"}
    )
    delete_response = client.delete("/api/notes/missing")

    assert update_response.status_code == 404
    assert update_response.get_json()["error"] == "Note not found."
    assert delete_response.status_code == 404


def test_validation(client):
    title_response = client.post("/api/notes", json={"title": "", "content": "Content"})
    content_response = client.post("/api/notes", json={"title": "Title", "content": "   "})
    json_response = client.post("/api/notes", data="not json", content_type="text/plain")

    assert title_response.status_code == 400
    assert title_response.get_json()["error"] == "Title is required."
    assert content_response.status_code == 400
    assert content_response.get_json()["error"] == "Note is required."
    assert json_response.status_code == 400
    assert json_response.get_json()["error"] == "Request body must be a JSON object."


def test_field_length_validation(client):
    title_response = client.post("/api/notes", json={"title": "t" * 81, "content": "Content"})
    content_response = client.post("/api/notes", json={"title": "Title", "content": "c" * 1001})

    assert title_response.status_code == 400
    assert title_response.get_json()["error"] == "Title must be 80 characters or fewer."
    assert content_response.status_code == 400
    assert content_response.get_json()["error"] == "Note must be 1000 characters or fewer."


def test_frontend_index_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Mini Notes" in response.data
