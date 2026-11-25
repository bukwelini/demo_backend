from __future__ import annotations

import time
import uuid

from flask import Blueprint, jsonify, request

from .database import get_db

notes_bp = Blueprint("notes", __name__, url_prefix="/api")
TITLE_LIMIT = 80
CONTENT_LIMIT = 1000


def now_ms() -> int:
    return int(time.time() * 1000)


def serialize_note(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def error_response(message: str, status: int):
    return jsonify({"error": message}), status


def parse_note_payload():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, error_response("Request body must be a JSON object.", 400)

    title = payload.get("title")
    content = payload.get("content")

    if not isinstance(title, str) or not title.strip():
        return None, error_response("Title is required.", 400)
    if not isinstance(content, str) or not content.strip():
        return None, error_response("Note is required.", 400)
    if len(title.strip()) > TITLE_LIMIT:
        return None, error_response(f"Title must be {TITLE_LIMIT} characters or fewer.", 400)
    if len(content.strip()) > CONTENT_LIMIT:
        return None, error_response(f"Note must be {CONTENT_LIMIT} characters or fewer.", 400)

    return {"title": title.strip(), "content": content.strip()}, None


@notes_bp.get("/notes")
def list_notes():
    rows = get_db().execute(
        "SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC"
    ).fetchall()
    return jsonify([serialize_note(row) for row in rows])


@notes_bp.post("/notes")
def create_note():
    data, error = parse_note_payload()
    if error:
        return error

    timestamp = now_ms()
    note = {
        "id": str(uuid.uuid4()),
        "title": data["title"],
        "content": data["content"],
        "created_at": timestamp,
        "updated_at": timestamp,
    }

    db = get_db()
    db.execute(
        "INSERT INTO notes (id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (note["id"], note["title"], note["content"], note["created_at"], note["updated_at"]),
    )
    db.commit()

    return jsonify(note), 201


@notes_bp.put("/notes/<note_id>")
def update_note(note_id: str):
    data, error = parse_note_payload()
    if error:
        return error

    db = get_db()
    existing = db.execute(
        "SELECT created_at, updated_at FROM notes WHERE id = ?", (note_id,)
    ).fetchone()
    if existing is None:
        return error_response("Note not found.", 404)

    note = {
        "id": note_id,
        "title": data["title"],
        "content": data["content"],
        "created_at": existing["created_at"],
        "updated_at": max(now_ms(), existing["updated_at"] + 1),
    }

    db.execute(
        "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
        (note["title"], note["content"], note["updated_at"], note_id),
    )
    db.commit()

    return jsonify(note)


@notes_bp.delete("/notes/<note_id>")
def delete_note(note_id: str):
    db = get_db()
    existing = db.execute("SELECT id FROM notes WHERE id = ?", (note_id,)).fetchone()
    if existing is None:
        return error_response("Note not found.", 404)

    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()

    return "", 204
