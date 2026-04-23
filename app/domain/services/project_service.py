import json
from typing import Any

from ..interfaces.repository import IProjectRepository, ISampleRepository
from ..models.project import Project


class ProjectService:
    def __init__(self, project_repo: IProjectRepository, sample_repo: ISampleRepository):
        self.project_repo = project_repo
        self.sample_repo = sample_repo

    def get_projects(self) -> list[Project]:
        return self.project_repo.get_projects()

    def get_project(self, project_id: int) -> Project | None:
        return self.project_repo.get_project(project_id)

    def create_project(
        self,
        name: str,
        description: str | None = None,
        classes: list[str] | None = None,
        commands: list[str] | None = None,
    ) -> int:
        p = Project(
            name=name,
            description=description,
            classes=classes or [],
            commands=commands or ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"],
        )
        return self.project_repo.create_project(p)

    def delete_project(self, project_id: int) -> None:
        self.sample_repo.delete_by_project(project_id)
        self.project_repo.delete_project(project_id)

    def get_classes(self, project_id: int) -> list[str]:
        p = self.get_project(project_id)
        return p.classes if p else []

    def update_classes(self, project_id: int, classes: list[str]) -> None:
        p = self.get_project(project_id)
        if p:
            p.classes = classes
            self.project_repo.update_project(p)

    def delete_class(self, project_id: int, class_index: int) -> dict[str, Any]:
        p = self.get_project(project_id)
        if not p or class_index < 0 or class_index >= len(p.classes):
            return {"status": "error", "message": "Invalid class index"}

        p.remove_class(class_index)
        self.project_repo.update_project(p)

        raw_samples = self.sample_repo.get_raw_samples_for_project(project_id)
        for row in raw_samples:
            sample_id = row["id"]
            data_str = row["data"]
            if not data_str:
                continue

            try:
                data = json.loads(data_str)
            except Exception:
                continue

            modified = False
            if "bboxes" in data:
                new_boxes = []
                for box in data["bboxes"]:
                    cat = box.get("category")
                    if cat is None:
                        new_boxes.append(box)
                        continue
                    if cat == class_index:
                        modified = True
                        continue
                    elif cat > class_index:
                        box["category"] = cat - 1
                        modified = True
                        new_boxes.append(box)
                    else:
                        new_boxes.append(box)
                if modified:
                    data["bboxes"] = new_boxes

            if modified:
                self.sample_repo.update_raw_sample_data(sample_id, json.dumps(data))

        return {"status": "success", "classes": p.classes}

    def get_commands(self, project_id: int) -> list[str]:
        p = self.get_project(project_id)
        return p.commands if p else ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]

    def update_commands(self, project_id: int, commands: list[str]) -> None:
        p = self.get_project(project_id)
        if p:
            p.commands = commands
            self.project_repo.update_project(p)

    def get_analytics(self, project_id: int) -> dict[str, Any]:
        p = self.get_project(project_id)
        classes = p.classes if p else []
        commands = p.commands if p else []

        raw_stats = self.sample_repo.get_analytics(project_id)

        class_distribution = []
        for class_id, count in raw_stats["class_distribution"].items():
            if int(class_id) < len(classes):
                name = classes[int(class_id)]
            else:
                name = f"Unknown-{class_id}"
            class_distribution.append({"id": int(class_id), "name": name, "count": count})
        class_distribution.sort(key=lambda x: x["count"], reverse=True)
        raw_stats["class_distribution"] = class_distribution

        command_distribution = []
        for cmd_id, count in raw_stats.get("command_distribution", {}).items():
            cmd_idx = int(cmd_id)
            if cmd_idx < len(commands):
                name = commands[cmd_idx]
            else:
                name = f"Unknown-{cmd_id}"
            command_distribution.append({"id": cmd_idx, "name": name, "count": count})
        command_distribution.sort(key=lambda x: x["count"], reverse=True)
        raw_stats["command_distribution"] = command_distribution

        return raw_stats

    def merge_projects(self, project_ids: list[int], new_name: str, new_description: str | None = None) -> int:
        """Merge multiple projects into a new one with unified classes."""
        source_projects = []
        for pid in project_ids:
            p = self.get_project(pid)
            if p:
                source_projects.append(p)

        if not source_projects:
            raise ValueError("No valid source projects found")

        # 1. Union of all classes and commands
        merged_classes = []
        for p in source_projects:
            for c in p.classes:
                if c not in merged_classes:
                    merged_classes.append(c)

        merged_commands = []
        for p in source_projects:
            for cmd in p.commands:
                if cmd not in merged_commands:
                    merged_commands.append(cmd)

        # 2. Create the new project
        new_project_id = self.create_project(new_name, new_description, merged_classes, merged_commands)

        # 3. For each project, map old IDs to new IDs and copy samples
        for p in source_projects:
            class_map = {old_idx: merged_classes.index(cname) for old_idx, cname in enumerate(p.classes)}
            command_map = {old_idx: merged_commands.index(cname) for old_idx, cname in enumerate(p.commands)}

            # Get all samples for this project
            samples = self.sample_repo.get_all_samples(limit=1000000, project_id=p.id)

            for s in samples:
                # To avoid filename collision in the new project, we could prefix it
                # but since image_name is PRIMARY KEY, we must ensure uniqueness.
                # If merging projects with same filenames, we'll prefix with project_id.
                new_filename = f"merged_{p.id}_{s.filename}"
                self.sample_repo.copy_sample_to_project(
                    s.filename, new_filename, new_project_id, class_map, command_map
                )

        return new_project_id
