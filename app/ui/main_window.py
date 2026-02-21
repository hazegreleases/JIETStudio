import tkinter as tk
from app.core.project_manager import ProjectManager
from app.core.settings_manager import SettingsManager
from app.ui.project_view import ProjectView
from app.ui.labeling_tool import LabelingTool
from app.ui.organized_labeling import OrganizedLabelingTool
from app.ui.training_view import TrainingView
from app.ui.inference_view import InferenceView
from app.ui.augmentation_view import AugmentationView
from app.ui.dataset_tools_view import DatasetToolsView
from app.ui.evaluation_view import EvaluationView
from app.ui.components import RoundedButton
from app.core.theme_manager import ThemeManager

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Jiet Studio")
        
        self.settings = SettingsManager()
        
        # Restore geometry
        geom = self.settings.get_setting("geometry", "1200x800")
        self.root.geometry(geom)
        
        # Track user-set geometry so tab switches don't reset it
        self._user_geometry = None
        
        self.theme = ThemeManager()
        self.root.configure(bg=self.theme.get("window_bg_color"))


        self.project_manager = ProjectManager()
        
        self.main_container = tk.Frame(self.root, bg=self.theme.get("window_bg_color"))
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.nav_bar = tk.Frame(self.root, bg=self.theme.get("window_bg_color"), height=40)
        # Don't pack nav bar yet, only show after project loaded

        self.views = {}
        self.current_view = None
        
        # Model management callbacks for training
        self.model_unload_callback = self.unload_background_models
        self.model_reload_callback = self.reload_background_models

        # Save geometry on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.show_project_view()

    def on_close(self):
        # Save window geometry
        self.settings.set_setting("geometry", self.root.geometry())
        self.root.destroy()

    def show_project_view(self):
        self.clear_view()
        self.nav_bar.pack_forget()
        self.views["project"] = ProjectView(self.main_container, self.project_manager, on_project_loaded=self.on_project_loaded)

    def on_project_loaded(self):
        self.setup_nav_bar()
        self.show_view("labeling")

    def setup_nav_bar(self):
        self._setup_menu()
        
        self.nav_bar.pack(side=tk.TOP, fill=tk.X)
        
        # Clear existing buttons if any
        for widget in self.nav_bar.winfo_children():
            widget.destroy()

        buttons = [
            ("Labeling", "labeling"),
            ("Training", "training"),
            ("Inference", "inference"),
            ("Augmentation", "augmentation"),
            ("Tools", "dataset_tools"),
            ("Evaluation", "evaluation"),
            ("Project", "project_settings") 
        ]

        for text, view_name in buttons:
            btn = RoundedButton(self.nav_bar, text=text, command=lambda v=view_name: self.show_view(v), 
                                width=100, height=30)
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Add project name label
        tk.Label(self.nav_bar, text=f"Project: {self.project_manager.project_config.get('name')}", 
                 bg=self.theme.get("window_bg_color"), fg=self.theme.get("window_text_color"), 
                 font=(self.theme.get("font_family"), int(self.theme.get("font_size_normal")))).pack(side=tk.RIGHT, padx=10)

    def _setup_menu(self):
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        jiet_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="JIET", menu=jiet_menu)
        jiet_menu.add_command(label="Settings", command=self.show_settings)
        
    def show_settings(self):
        from app.ui.settings_window import SettingsWindow
        SettingsWindow(self.root, self.project_manager, self.settings)


    def show_view(self, view_name):
        # Save current geometry before switching
        self._user_geometry = self.root.geometry()
        
        self.clear_view()

        if view_name == "project_settings":
            self.show_project_view()
            return

        if view_name == "labeling":
            self.views[view_name] = OrganizedLabelingTool(self.main_container, self.project_manager)
        elif view_name == "training":
            self.views[view_name] = TrainingView(
                self.main_container, 
                self.project_manager,
                unload_callback=self.model_unload_callback,
                reload_callback=self.model_reload_callback
            )
        elif view_name == "inference":
            self.views[view_name] = InferenceView(self.main_container, self.project_manager)
        elif view_name == "augmentation":
            self.views[view_name] = AugmentationView(self.main_container, self.project_manager)
        elif view_name == "dataset_tools":
            self.views[view_name] = DatasetToolsView(self.main_container, self.project_manager)
        elif view_name == "evaluation":
            self.views[view_name] = EvaluationView(self.main_container, self.project_manager)
        
        self.views[view_name].pack(fill=tk.BOTH, expand=True)
        self.current_view = self.views[view_name]
        
        # Restore saved geometry so window size doesn't reset
        if self._user_geometry:
            self.root.geometry(self._user_geometry)

    def clear_view(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
        # Clear references to destroyed views to prevent stale access
        self.views.clear()
        self.current_view = None
    
    def unload_background_models(self):
        """Unload all background models to free memory for training."""
        print("[Memory Manager] Unloading background models...")
        
        # Unload SAM from organized labeling if it exists
        if "labeling" in self.views and hasattr(self.views["labeling"], 'unload_sam'):
            self.views["labeling"].unload_sam()
        
        # Unload any inference models if view exists
        if "inference" in self.views and hasattr(self.views["inference"], 'unload_model'):
            try:
                self.views["inference"].unload_model()
            except:
                pass
        
        # Aggressive memory cleanup
        import gc
        import torch
        
        print("[Memory Manager] Running garbage collection...")
        gc.collect()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            print("[Memory Manager] Clearing CUDA cache...")
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        
        # Final garbage collection
        gc.collect()
        
        print("[Memory Manager] Background models unloaded and memory cleaned")
    
    def reload_background_models(self):
        """Reload background models after training completes."""
        print("[Memory Manager] Reloading background models...")
        
        # Reload SAM for Magic Wand functionality
        if "labeling" in self.views and hasattr(self.views["labeling"], 'reload_sam'):
            self.views["labeling"].reload_sam()
        
        print("[Memory Manager] Background models reloaded")
