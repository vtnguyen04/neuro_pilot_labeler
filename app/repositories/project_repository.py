import json
from typing import List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..domain.interfaces.repository import IProjectRepository
from ..domain.models.project import Project

class ProjectRepository(BaseRepository, IProjectRepository):
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    classes TEXT DEFAULT '[]',
                    commands TEXT DEFAULT '["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor = conn.execute("PRAGMA table_info(projects)")
            cols = [row['name'] for row in cursor.fetchall()]
            if 'classes' not in cols:
                conn.execute("ALTER TABLE projects ADD COLUMN classes TEXT DEFAULT '[]'")
            if 'commands' not in cols:
                conn.execute("ALTER TABLE projects ADD COLUMN commands TEXT DEFAULT '[\"FOLLOW_LANE\", \"TURN_LEFT\", \"TURN_RIGHT\", \"STRAIGHT\"]'")
            conn.commit()

    def _row_to_entity(self, row: dict) -> Project:
        try:
            classes = json.loads(row.get('classes', '[]'))
        except json.JSONDecodeError:
            classes = []
            
        try:
            commands = json.loads(row.get('commands', '[]'))
            if not commands:
                commands = ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]
        except json.JSONDecodeError:
            commands = ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]

        return Project(
            id=row['id'],
            name=row['name'],
            description=row.get('description'),
            classes=classes,
            commands=commands,
            created_at=row.get('created_at')
        )

    def create_project(self, project: Project) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO projects (name, description, classes, commands) VALUES (?, ?, ?, ?)",
                (project.name, project.description, json.dumps(project.classes), json.dumps(project.commands))
            )
            project_id = cursor.lastrowid
            conn.commit()
            return project_id

    def get_projects(self) -> List[Project]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM projects").fetchall()
            return [self._row_to_entity(dict(row)) for row in rows]

    def get_project(self, project_id: int) -> Optional[Project]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                return None
            return self._row_to_entity(dict(row))

    def delete_project(self, project_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()

    def update_project(self, project: Project) -> None:
        if project.id is None:
            raise ValueError("Cannot update a project without an ID")
            
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE projects SET name = ?, description = ?, classes = ?, commands = ? WHERE id = ?", 
                (project.name, project.description, json.dumps(project.classes), json.dumps(project.commands), project.id)
            )
            conn.commit()

    def get_classes(self, project_id: int) -> List[str]:
        p = self.get_project(project_id)
        return p.classes if p else []

    def update_classes(self, project_id: int, classes: List[str]):
        p = self.get_project(project_id)
        if p:
            p.classes = classes
            self.update_project(p)

    def get_commands(self, project_id: int) -> List[str]:
        p = self.get_project(project_id)
        return p.commands if p else ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]

    def update_commands(self, project_id: int, commands: List[str]):
        p = self.get_project(project_id)
        if p:
            p.commands = commands
            self.update_project(p)
