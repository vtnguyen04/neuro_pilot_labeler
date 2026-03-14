
from ..domain.interfaces.repository import IVersionRepository
from .base_repository import BaseRepository


class VersionRepository(BaseRepository, IVersionRepository):
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dataset_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    project_id INTEGER NOT NULL,
                    path TEXT,
                    sample_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            cursor = conn.execute("PRAGMA table_info(dataset_versions)")
            cols = [row["name"] for row in cursor.fetchall()]

            if "path" not in cols:
                conn.execute("ALTER TABLE dataset_versions ADD COLUMN path TEXT")
            if "name" not in cols:
                conn.execute("ALTER TABLE dataset_versions ADD COLUMN name TEXT")
            if "description" not in cols:
                conn.execute("ALTER TABLE dataset_versions ADD COLUMN description TEXT")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS version_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_id INTEGER NOT NULL,
                    sample_name TEXT NOT NULL,
                    data TEXT,
                    split TEXT,
                    FOREIGN KEY (version_id) REFERENCES dataset_versions(id)
                )
            """)
            conn.commit()

    def create_version(self, name: str, description: str, project_id: int, path: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO dataset_versions (name, description, project_id, path) VALUES (?, ?, ?, ?)",
                (name, description, project_id, path),
            )
            return cursor.lastrowid

    def list_versions(self, project_id: int | None = None) -> list[dict]:
        with self._get_connection() as conn:
            if project_id:
                rows = conn.execute(
                    "SELECT * FROM dataset_versions WHERE project_id = ? ORDER BY created_at DESC", (project_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM dataset_versions ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def get_version(self, version_id: int) -> dict | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM dataset_versions WHERE id = ?", (version_id,)).fetchone()
            return dict(row) if row else None

    def delete_version(self, version_id: int):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM version_items WHERE version_id = ?", (version_id,))
            conn.execute("DELETE FROM dataset_versions WHERE id = ?", (version_id,))
            conn.commit()

    def add_item_to_version(self, version_id: int, sample_name: str, data: str, split: str):
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO version_items (version_id, sample_name, data, split)
                VALUES (?, ?, ?, ?)
            """,
                (version_id, sample_name, data, split),
            )
            conn.commit()

    def update_sample_count(self, version_id: int, count: int):
        with self._get_connection() as conn:
            conn.execute("UPDATE dataset_versions SET sample_count = ? WHERE id = ?", (count, version_id))
            conn.commit()
