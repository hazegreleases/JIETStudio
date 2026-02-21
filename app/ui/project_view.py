import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from app.ui.components import RoundedButton
from app.core.theme_manager import ThemeManager
import os

class ProjectView(tk.Frame):
    def __init__(self, parent, project_manager, on_project_loaded):
        super().__init__(parent)
        self.project_manager = project_manager
        self.on_project_loaded = on_project_loaded
        self.theme = ThemeManager()
        self.pack(fill=tk.BOTH, expand=True)

        self._create_ui()

    def _create_ui(self):
        self.configure(bg=self.theme.get("window_bg_color"))
        
        # Main Container
        container = tk.Frame(self, bg=self.theme.get("window_bg_color"))
        container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Header
        header_frame = tk.Frame(container, bg=self.theme.get("window_bg_color"))
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text="Projects Hub", 
                 font=(self.theme.get("font_family"), int(self.theme.get("font_size_header")), "bold"), 
                 bg=self.theme.get("window_bg_color"), fg=self.theme.get("window_text_color")).pack(side=tk.LEFT)

        # Action Buttons (Top Right)
        action_frame = tk.Frame(header_frame, bg=self.theme.get("window_bg_color"))
        action_frame.pack(side=tk.RIGHT)
        
        RoundedButton(action_frame, text="New Project", command=self.create_project, width=120, height=35).pack(side=tk.LEFT, padx=5)
        RoundedButton(action_frame, text="Open Project", command=self.load_project, width=120, height=35).pack(side=tk.LEFT, padx=5)

        # Recent Projects List
        tk.Label(container, text="Recent Projects", 
                 font=(self.theme.get("font_family"), int(self.theme.get("font_size_normal")), "bold"), 
                 bg=self.theme.get("window_bg_color"), fg=self.theme.get("window_text_color")).pack(anchor=tk.W, pady=(10, 5))

        self.recent_frame = tk.Frame(container, bg=self.theme.get("window_bg_color"))
        self.recent_frame.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_recent_projects()

    def refresh_recent_projects(self):
        for widget in self.recent_frame.winfo_children():
            widget.destroy()
            
        recent = self.project_manager.recent_projects
        if not recent:
            tk.Label(self.recent_frame, text="No recent projects found.", 
                     bg=self.theme.get("window_bg_color"), fg="#888").pack(pady=20)
            return

        canvas = tk.Canvas(self.recent_frame, bg=self.theme.get("window_bg_color"), highlightthickness=0)
        scrollbar = tk.Scrollbar(self.recent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.get("window_bg_color"))

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for path in recent:
            self._create_project_item(scrollable_frame, path)

    def _create_project_item(self, parent, path):
        item_bg = self.theme.get("button_bg_color")
        item_fg = self.theme.get("button_text_color")
        item_frame = tk.Frame(parent, bg=item_bg, pady=5, padx=5)
        item_frame.pack(fill=tk.X, pady=2, padx=5)
        
        name = os.path.basename(path)
        
        info_frame = tk.Frame(item_frame, bg=item_bg)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(info_frame, text=name, font=(self.theme.get("font_family"), 11, "bold"), bg=item_bg, fg=item_fg).pack(anchor=tk.W)
        tk.Label(info_frame, text=path, font=(self.theme.get("font_family"), 9), bg=item_bg, fg="#aaa").pack(anchor=tk.W)
        
        btn_frame = tk.Frame(item_frame, bg=item_bg)
        btn_frame.pack(side=tk.RIGHT)

        RoundedButton(btn_frame, text="Open", command=lambda p=path: self.open_recent(p), width=80, height=30).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="X", command=lambda p=path: self.remove_recent(p), width=30, height=30, bg_color="#552222").pack(side=tk.LEFT, padx=5)

    def open_recent(self, path):
        if not os.path.exists(path):
            if messagebox.askyesno("Error", "Project path does not exist. Remove from list?"):
                self.remove_recent(path)
            return
            
        try:
            self.project_manager.load_project(path)
            self.on_project_loaded()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_recent(self, path):
        self.project_manager.remove_recent_project(path)
        self.refresh_recent_projects()

    def create_project(self):
        path = filedialog.askdirectory(title="Select Parent Directory for New Project")
        if not path: return

        name = simpledialog.askstring("Project Name", "Enter Project Name:")
        if not name: return

        try:
            self.project_manager.create_project(path, name)
            messagebox.showinfo("Success", f"Project '{name}' created successfully!")
            self.on_project_loaded()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_project(self):
        path = filedialog.askdirectory(title="Select Project Directory")
        if not path: return

        try:
            self.project_manager.load_project(path)
            self.on_project_loaded()
        except Exception as e:
            messagebox.showerror("Error", str(e))
