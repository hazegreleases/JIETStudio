import os

class ThemeManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance.colors = {}
            cls._instance.load_theme()
        return cls._instance

    def load_theme(self):
        theme_path = "theme.txt"
        if not os.path.exists(theme_path):
            # Defaults
            self.colors = {
                "window_bg_color": "#FFFFFF",
                "window_text_color": "#333333",
                "button_bg_color": "#067BC2",
                "button_hover_color": "#CAC4CE",
                "button_click_color": "#22223B",
                "button_text_color": "#FFFFFF",
                "font_family": "Inter",
                "font_size_normal": "10",
                "font_size_large": "12",
                "font_size_header": "24",
                "inspector_non_labeled_color": "#FFCCCC"
            }
            return

        with open(theme_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    self.colors[key.strip()] = value.strip()

    def get(self, key):
        return self.colors.get(key, "#000000") # Default black if missing
