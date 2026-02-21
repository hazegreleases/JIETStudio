import os
import yaml
import shutil
from datetime import datetime

class ProjectManager:
    def __init__(self):
        self.current_project_path = None
        self.project_config = {}
        # Use AppData for persistence
        appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'JIETStudio')
        os.makedirs(appdata_dir, exist_ok=True)
        self.recent_projects_file = os.path.join(appdata_dir, "recent_projects.txt")
        self.recent_projects = self.load_recent_projects()

    def create_project(self, path, name):
        """Creates a new project directory structure."""
        full_path = os.path.join(path, name)
        if os.path.exists(full_path):
            raise FileExistsError(f"Project '{name}' already exists at {path}")

        os.makedirs(full_path)
        os.makedirs(os.path.join(full_path, "data", "images"))
        os.makedirs(os.path.join(full_path, "data", "labels"))
        os.makedirs(os.path.join(full_path, "models"))
        os.makedirs(os.path.join(full_path, "exports"))

        config = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "classes": []
        }
        
        self._save_config(full_path, config)
        self.load_project(full_path)
        return full_path

    def load_project(self, path):
        """Loads an existing project."""
        config_path = os.path.join(path, "project_config.yaml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Not a valid project: {path}")

        with open(config_path, "r") as f:
            self.project_config = yaml.safe_load(f)
        
        self.current_project_path = path
        self.add_recent_project(path)
        return self.project_config

    def save_project(self):
        """Saves current project configuration."""
        if self.current_project_path:
            self._save_config(self.current_project_path, self.project_config)

    def _save_config(self, path, config):
        with open(os.path.join(path, "project_config.yaml"), "w") as f:
            yaml.dump(config, f)

    def get_classes(self):
        return self.project_config.get("classes", [])

    def add_class(self, class_name):
        if class_name not in self.project_config.get("classes", []):
            self.project_config.setdefault("classes", []).append(class_name)
            self.save_project()

    def remove_class(self, class_name):
        if class_name in self.project_config.get("classes", []):
            self.project_config["classes"].remove(class_name)
            self.save_project()

    def get_setting(self, key, default=None):
        """Get a setting from project config."""
        return self.project_config.get("settings", {}).get(key, default)

    def set_setting(self, key, value):
        """Set a setting in project config."""
        if "settings" not in self.project_config:
            self.project_config["settings"] = {}
        self.project_config["settings"][key] = value
        self.save_project()

    def load_recent_projects(self):
        if os.path.exists(self.recent_projects_file):
            try:
                import json
                with open(self.recent_projects_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_recent_projects(self):
        import json
        os.makedirs(os.path.dirname(self.recent_projects_file), exist_ok=True)
        with open(self.recent_projects_file, "w") as f:
            json.dump(self.recent_projects, f)

    def add_recent_project(self, path):
        # Remove if exists to move to top
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        # Keep only last 10
        self.recent_projects = self.recent_projects[:10]
        self.save_recent_projects()

    def remove_recent_project(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
            self.save_recent_projects()
