import json
from typing import List, Optional, Dict, Any
from ..interfaces.repository import IProjectRepository, ISampleRepository
from ..models.project import Project

class ProjectService:
    def __init__(self, project_repo: IProjectRepository, sample_repo: ISampleRepository):
        self.project_repo = project_repo
        self.sample_repo = sample_repo

    def get_projects(self) -> List[Project]:
        return self.project_repo.get_projects()

    def get_project(self, project_id: int) -> Optional[Project]:
        return self.project_repo.get_project(project_id)

    def create_project(self, name: str, description: Optional[str] = None, classes: Optional[List[str]] = None, commands: Optional[List[str]] = None) -> int:
        p = Project(
            name=name,
            description=description,
            classes=classes or [],
            commands=commands or ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]
        )
        return self.project_repo.create_project(p)

    def delete_project(self, project_id: int) -> None:
        self.sample_repo.delete_by_project(project_id)
        self.project_repo.delete_project(project_id)

    def get_classes(self, project_id: int) -> List[str]:
        p = self.get_project(project_id)
        return p.classes if p else []

    def update_classes(self, project_id: int, classes: List[str]) -> None:
        p = self.get_project(project_id)
        if p:
            p.classes = classes
            self.project_repo.update_project(p)

    def delete_class(self, project_id: int, class_index: int) -> Dict[str, Any]:
        p = self.get_project(project_id)
        if not p or class_index < 0 or class_index >= len(p.classes):
            return {"status": "error", "message": "Invalid class index"}

        p.remove_class(class_index)
        self.project_repo.update_project(p)

        raw_samples = self.sample_repo.get_raw_samples_for_project(project_id)
        for row in raw_samples:
            sample_id = row['id']
            data_str = row['data']
            if not data_str:
                continue
                
            try:
                data = json.loads(data_str)
            except:
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

    def get_commands(self, project_id: int) -> List[str]:
        p = self.get_project(project_id)
        return p.commands if p else ["FOLLOW_LANE", "TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]

    def update_commands(self, project_id: int, commands: List[str]) -> None:
        p = self.get_project(project_id)
        if p:
            p.commands = commands
            self.project_repo.update_project(p)

    def get_analytics(self, project_id: int) -> Dict[str, Any]:
        p = self.get_project(project_id)
        classes = p.classes if p else []
        commands = p.commands if p else []
        
        raw_stats = self.sample_repo.get_analytics(project_id)

        class_distribution = []
        for class_id, count in raw_stats['class_distribution'].items():
            if int(class_id) < len(classes):
                name = classes[int(class_id)]
            else:
                name = f"Unknown-{class_id}"
            class_distribution.append({"id": int(class_id), "name": name, "count": count})
        class_distribution.sort(key=lambda x: x['count'], reverse=True)
        raw_stats['class_distribution'] = class_distribution

        command_distribution = []
        for cmd_id, count in raw_stats.get('command_distribution', {}).items():
            cmd_idx = int(cmd_id)
            if cmd_idx < len(commands):
                name = commands[cmd_idx]
            else:
                name = f"Unknown-{cmd_id}"
            command_distribution.append({"id": cmd_idx, "name": name, "count": count})
        command_distribution.sort(key=lambda x: x['count'], reverse=True)
        raw_stats['command_distribution'] = command_distribution

        return raw_stats
