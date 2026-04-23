import sqlite3
from typing import Any

from ..domain.interfaces.repository import ISampleRepository
from ..domain.models.sample import Sample
from .base_repository import BaseRepository


class SampleRepository(BaseRepository, ISampleRepository):
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS samples (
                    image_name TEXT PRIMARY KEY,
                    image_path TEXT,
                    project_id INTEGER,
                    data TEXT,
                    is_labeled BOOLEAN DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_is_labeled ON samples(is_labeled)")
            conn.commit()

    def get_all_samples(
        self,
        limit: int = 100,
        offset: int = 0,
        is_labeled: bool | None = None,
        split: str | None = None,
        project_id: int | None = None,
        class_id: int | None = None,
        command: int | None = None,
        has_control_points: bool | None = None,
    ) -> list[Sample]:
        query = "SELECT image_name as filename, is_labeled, updated_at, data, image_path, project_id FROM samples"
        where_clauses = []
        params = []

        if is_labeled is not None:
            where_clauses.append("is_labeled = ?")
            params.append(1 if is_labeled else 0)

        if split:
            where_clauses.append("image_path LIKE ?")
            params.append(f"%/{split}/%")

        if project_id is not None:
            where_clauses.append("project_id = ?")
            params.append(project_id)

        if class_id is not None:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM json_each(data, '$.bboxes') WHERE json_extract(value, '$.category') = ?)"
            )
            params.append(class_id)

        if command is not None:
            where_clauses.append("json_extract(data, '$.command') = ?")
            params.append(command)

        if has_control_points is not None:
            if has_control_points:
                where_clauses.append("json_array_length(json_extract(data, '$.control_points')) > 0")
            else:
                # Handle both null, non-existent, and empty array
                where_clauses.append(
                    "(json_extract(data, '$.control_points') IS NULL OR "
                    "json_type(data, '$.control_points') IS NULL OR "
                    "json_array_length(json_extract(data, '$.control_points')) = 0)"
                )

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [Sample.from_row(dict(row)) for row in rows]

    def get_sample(self, filename: str) -> Sample | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT image_name as filename, * FROM samples WHERE image_name = ?", (filename,)
            ).fetchone()
            if not row:
                return None
            return Sample.from_row(dict(row))

    def add_sample(self, sample: Sample) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO samples (image_name, image_path, project_id, data, is_labeled) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    sample.filename,
                    sample.image_path,
                    sample.project_id,
                    sample.label_data.to_json_str(),
                    1 if sample.is_labeled else 0,
                ),
            )
            conn.commit()

    def save_label(self, sample: Sample) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE samples SET data = ?, is_labeled = ?, updated_at = CURRENT_TIMESTAMP WHERE image_name = ?",
                (sample.label_data.to_json_str(), 1 if sample.is_labeled else 0, sample.filename),
            )
            conn.commit()

    def delete_sample(self, filename: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM samples WHERE image_name = ?", (filename,))
            conn.commit()

    def delete_samples(
        self,
        is_labeled: bool | None = None,
        split: str | None = None,
        project_id: int | None = None,
        class_id: int | None = None,
        command: int | None = None,
        has_control_points: bool | None = None,
    ) -> list[str]:
        """Delete samples based on filters and return the list of filenames."""
        where_clauses = []
        params = []

        if is_labeled is not None:
            where_clauses.append("is_labeled = ?")
            params.append(1 if is_labeled else 0)

        if split:
            where_clauses.append("image_path LIKE ?")
            params.append(f"%/{split}/%")

        if project_id is not None:
            where_clauses.append("project_id = ?")
            params.append(project_id)

        if class_id is not None:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM json_each(data, '$.bboxes') WHERE json_extract(value, '$.category') = ?)"
            )
            params.append(class_id)

        if command is not None:
            where_clauses.append("json_extract(data, '$.command') = ?")
            params.append(command)

        if has_control_points is not None:
            if has_control_points:
                where_clauses.append("json_array_length(json_extract(data, '$.control_points')) > 0")
            else:
                # Handle both null, non-existent, and empty array
                where_clauses.append(
                    "(json_extract(data, '$.control_points') IS NULL OR "
                    "json_type(data, '$.control_points') IS NULL OR "
                    "json_array_length(json_extract(data, '$.control_points')) = 0)"
                )

        if not where_clauses:
            return []  # Prevent accidental delete all

        # First get filenames to handle physical file cleanup later
        select_query = "SELECT image_name FROM samples WHERE " + " AND ".join(where_clauses)
        delete_query = "DELETE FROM samples WHERE " + " AND ".join(where_clauses)

        with self._get_connection() as conn:
            rows = conn.execute(select_query, params).fetchall()
            filenames = [r["image_name"] for r in rows]
            conn.execute(delete_query, params)
            conn.commit()
            return filenames

    def duplicate_sample(self, filename: str, new_filename: str):
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM samples WHERE image_name = ?", (filename,)).fetchone()
            if row:
                try:
                    conn.execute(
                        "INSERT INTO samples (image_name, image_path, project_id, data, is_labeled) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (new_filename, row["image_path"], row["project_id"], row["data"], row["is_labeled"]),
                    )
                    conn.commit()
                except sqlite3.IntegrityError:
                    pass

    def count_references_to_path(self, image_path: str) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM samples WHERE image_path = ?", (image_path,)).fetchone()
            return row[0]

    def delete_by_project(self, project_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM samples WHERE project_id = ?", (project_id,))
            conn.commit()

    def get_stats(self, project_id: int | None = None) -> dict[str, Any]:
        with self._get_connection() as conn:

            def get_count(split: str | None = None, labeled: bool | None = None):
                q = "SELECT COUNT(*) FROM samples"
                clauses = []
                p = []
                if split:
                    clauses.append("image_path LIKE ?")
                    p.append(f"%/{split}/%")
                if labeled is not None:
                    clauses.append("is_labeled = ?")
                    p.append(1 if labeled else 0)
                if project_id:
                    clauses.append("project_id = ?")
                    p.append(project_id)

                if clauses:
                    q += " WHERE " + " AND ".join(clauses)
                return conn.execute(q, p).fetchone()[0]

            return {
                "raw": get_count("raw"),
                "train": get_count("train"),
                "val": get_count("val"),
                "test": get_count("test"),
                "labeled": get_count(labeled=True),
                "total": get_count(),
            }

    def get_analytics(self, project_id: int) -> dict[str, Any]:
        with self._get_connection() as conn:
            class_dist_query = """
                SELECT
                    json_extract(value, '$.category') as class_id,
                    COUNT(*) as count
                FROM samples, json_each(data, '$.bboxes')
                WHERE project_id = ?
                GROUP BY class_id
            """
            class_dist_rows = conn.execute(class_dist_query, (project_id,)).fetchall()
            class_dist = {row["class_id"]: row["count"] for row in class_dist_rows}

            cmd_dist_query = """
                SELECT
                    json_extract(data, '$.command') as command_id,
                    COUNT(*) as count
                FROM samples
                WHERE project_id = ? AND is_labeled = 1
                GROUP BY command_id
            """
            cmd_dist_rows = conn.execute(cmd_dist_query, (project_id,)).fetchall()
            cmd_dist = {row["command_id"]: row["count"] for row in cmd_dist_rows if row["command_id"] is not None}

            stats_query = """
                SELECT
                    COUNT(*) as total_samples,
                    SUM(is_labeled) as labeled_samples,
                    SUM(json_array_length(json_extract(data, '$.bboxes'))) as total_bboxes,
                    SUM(json_array_length(json_extract(data, '$.waypoints'))) as total_waypoints
                FROM samples
                WHERE project_id = ?
            """
            stats_row = conn.execute(stats_query, (project_id,)).fetchone()

            wp_samples_query = """
                SELECT COUNT(*)
                FROM samples
                WHERE project_id = ? AND json_array_length(json_extract(data, '$.waypoints')) > 0
            """
            wp_samples = conn.execute(wp_samples_query, (project_id,)).fetchone()[0]

            return {
                "class_distribution": class_dist,
                "command_distribution": cmd_dist,
                "total_samples": stats_row["total_samples"],
                "labeled_samples": stats_row["labeled_samples"],
                "total_bboxes": stats_row["total_bboxes"] or 0,
                "total_waypoints": stats_row["total_waypoints"] or 0,
                "samples_with_waypoints": wp_samples,
            }

    def get_raw_samples_for_project(self, project_id: int) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT rowid as id, data FROM samples WHERE project_id = ? AND data IS NOT NULL", (project_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def update_raw_sample_data(self, sample_id: int, raw_data_str: str) -> None:
        with self._get_connection() as conn:
            conn.execute("UPDATE samples SET data = ? WHERE rowid = ?", (raw_data_str, sample_id))
            conn.commit()

    def delete_unlabeled_samples(self, project_id: int | None = None) -> int:
        """Delete all samples where is_labeled = 0. Optionally filter by project_id."""
        with self._get_connection() as conn:
            if project_id is not None:
                cursor = conn.execute(
                    "DELETE FROM samples WHERE is_labeled = 0 AND project_id = ?",
                    (project_id,)
                )
            else:
                cursor = conn.execute("DELETE FROM samples WHERE is_labeled = 0")
            conn.commit()
            return cursor.rowcount

    def reset_label(self, filename: str):
        sample = self.get_sample(filename)
        if sample:
            sample.reset_label()
            self.save_label(sample)

    def copy_sample_to_project(
        self,
        filename: str,
        new_filename: str,
        new_project_id: int,
        class_map: dict[int, int],
        command_map: dict[int, int],
    ) -> None:
        """Copy a sample to a new project with re-mapped class and command IDs."""
        sample = self.get_sample(filename)
        if not sample:
            return

        # Map class IDs in bboxes
        for bbox in sample.label_data.bboxes:
            if bbox.category in class_map:
                bbox.category = class_map[bbox.category]

        # Map command ID
        if sample.label_data.command in command_map:
            sample.label_data.command = command_map[sample.label_data.command]

        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO samples (image_name, image_path, project_id, data, is_labeled) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        new_filename,
                        sample.image_path,
                        new_project_id,
                        sample.label_data.to_json_str(),
                        1 if sample.is_labeled else 0,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # If new_filename already exists, skip or handle accordingly
                pass
