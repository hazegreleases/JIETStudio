import os
import json

class SettingsManager:
    def __init__(self):
        # Determine AppData path
        self.appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'JIETStudio')
        os.makedirs(self.appdata_dir, exist_ok=True)
        
        self.settings_path = os.path.join(self.appdata_dir, 'settings.txt')
        self.recent_projects_path = os.path.join(self.appdata_dir, 'recent_projects.txt')
        
        self.settings = self._load_json(self.settings_path)
        self.recent_projects = self._load_json(self.recent_projects_path, default=[])

    def _load_json(self, path, default=None):
        if default is None: default = {}
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def _save_json(self, path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings to {path}: {e}")

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        self.settings[key] = value
        self._save_json(self.settings_path, self.settings)

    def get_recent_projects(self):
        return self.recent_projects

    def add_recent_project(self, project_path):
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
        self.recent_projects.insert(0, project_path)
        self.recent_projects = self.recent_projects[:10]  # Keep last 10
        self._save_json(self.recent_projects_path, self.recent_projects)
