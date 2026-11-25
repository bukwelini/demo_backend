from __future__ import annotations

import os

from flask import Flask, send_from_directory

from .database import close_db, init_db
from .routes import notes_bp


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    default_frontend_dir = os.path.abspath(os.path.join(app.root_path, "..", "..", "frontend"))
    app.config.from_mapping(
        DATABASE=os.environ.get("NOTES_DB", os.path.join(app.instance_path, "notes.sqlite3")),
        FRONTEND_DIR=os.environ.get("FRONTEND_DIR", default_frontend_dir),
        SERVE_FRONTEND=os.environ.get("SERVE_FRONTEND", "1") == "1",
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    database_path = app.config["DATABASE"]
    if database_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)

    frontend_dir = os.path.abspath(app.config["FRONTEND_DIR"])

    app.register_blueprint(notes_bp)
    app.teardown_appcontext(close_db)

    if app.config["SERVE_FRONTEND"] and os.path.isdir(frontend_dir):

        @app.get("/")
        def index():
            return send_from_directory(frontend_dir, "index.html")

        @app.get("/<path:path>")
        def frontend_file(path: str):
            return send_from_directory(frontend_dir, path)

    with app.app_context():
        init_db()

    return app
