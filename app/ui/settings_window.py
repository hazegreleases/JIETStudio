import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import torch
from app.ui.components import RoundedButton
from app.core.theme_manager import ThemeManager

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, project_manager, settings_manager):
        super().__init__(parent)
        self.project_manager = project_manager
        self.settings = settings_manager
        self.theme = ThemeManager()
        
        self.title("Settings")
        self.geometry("500x300")
        self.configure(bg=self.theme.get("window_bg_color"))
        
        # Modal behavior
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        main_frame = tk.Frame(self, bg=self.theme.get("window_bg_color"), padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Auto-Label Model
        model_frame = tk.LabelFrame(main_frame, text="Auto-Labeling", 
                                    bg=self.theme.get("window_bg_color"),
                                    fg=self.theme.get("window_text_color"),
                                    font=(self.theme.get("font_family"), 12, "bold"))
        model_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(model_frame, text="YOLO Model Path:", 
                 bg=self.theme.get("window_bg_color"),
                 fg=self.theme.get("window_text_color")).pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        input_frame = tk.Frame(model_frame, bg=self.theme.get("window_bg_color"))
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.model_path_var = tk.StringVar()
        entry = tk.Entry(input_frame, textvariable=self.model_path_var, width=40)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        RoundedButton(input_frame, text="Browse", command=self.browse_model, width=80, height=25).pack(side=tk.RIGHT)
        
        # Confidence
        tk.Label(model_frame, text="Confidence Threshold:", 
                 bg=self.theme.get("window_bg_color"),
                 fg=self.theme.get("window_text_color")).pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        conf_frame = tk.Frame(model_frame, bg=self.theme.get("window_bg_color"))
        conf_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.conf_var = tk.DoubleVar(value=0.5)
        
        scale = ttk.Scale(conf_frame, from_=0.1, to=1.0, variable=self.conf_var, orient=tk.HORIZONTAL)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.conf_label = tk.Label(conf_frame, text="0.50", width=5,
                                   bg=self.theme.get("window_bg_color"),
                                   fg=self.theme.get("window_text_color"))
        self.conf_label.pack(side=tk.RIGHT, padx=5)
        
        # Trace var to update label
        self.conf_var.trace_add("write", self._update_conf_label)
        
        # Hardware Acceleration
        hw_frame = tk.LabelFrame(main_frame, text="Hardware Acceleration", 
                                    bg=self.theme.get("window_bg_color"),
                                    fg=self.theme.get("window_text_color"),
                                    font=(self.theme.get("font_family"), 12, "bold"))
        hw_frame.pack(fill=tk.X, pady=10)

        # Use CUDA
        self.use_cuda_var = tk.BooleanVar(value=True)
        self.cuda_check = tk.Checkbutton(hw_frame, text="Use CUDA in Labeling (Auto-Label & SAM)", 
                                         variable=self.use_cuda_var,
                                         bg=self.theme.get("window_bg_color"),
                                         fg=self.theme.get("window_text_color"),
                                         selectcolor="#333",
                                         activebackground=self.theme.get("window_bg_color"),
                                         activeforeground=self.theme.get("window_text_color"))
        self.cuda_check.pack(anchor=tk.W, padx=10, pady=5)
        
        if not torch.cuda.is_available():
            self.use_cuda_var.set(False)
            self.cuda_check.config(state="disabled", text="Use CUDA in Labeling (Not Available)")

        # Workers
        total_threads = os.cpu_count() or 4
        default_workers = max(1, total_threads // 2)
        
        tk.Label(hw_frame, text=f"Workers (Labeling/Augmentation):", 
                 bg=self.theme.get("window_bg_color"),
                 fg=self.theme.get("window_text_color")).pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        workers_frame = tk.Frame(hw_frame, bg=self.theme.get("window_bg_color"))
        workers_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.workers_var = tk.IntVar(value=default_workers)
        worker_spin = ttk.Spinbox(workers_frame, from_=1, to=total_threads, textvariable=self.workers_var, width=10)
        worker_spin.pack(side=tk.LEFT)
        
        tk.Label(workers_frame, text=f"(System Threads: {total_threads})", 
                 bg=self.theme.get("window_bg_color"),
                 fg="#888").pack(side=tk.LEFT, padx=10)

        # Save/Close Buttons
        btn_frame = tk.Frame(main_frame, bg=self.theme.get("window_bg_color"))
        btn_frame.pack(fill=tk.X, pady=20)
        
        # Push to right
        tk.Frame(btn_frame, bg=self.theme.get("window_bg_color")).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        RoundedButton(btn_frame, text="Save", command=self.save_settings, width=80, height=30).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="Cancel", command=self.destroy, width=80, height=30).pack(side=tk.LEFT, padx=5)

    def _update_conf_label(self, *args):
        self.conf_label.config(text=f"{self.conf_var.get():.2f}")

    def _load_values(self):
        # Load from GLOBAL settings manager (AppData)
        model = self.settings.get_setting("auto_label_model", "")
        conf = self.settings.get_setting("auto_label_confidence", 0.5)
        
        self.model_path_var.set(model)
        self.conf_var.set(float(conf))
        
        # Load Hardware settings
        use_cuda = str(self.settings.get_setting("use_cuda_labeling", str(torch.cuda.is_available())))
        workers = self.settings.get_setting("labeling_workers", max(1, (os.cpu_count() or 4) // 2))
        
        if torch.cuda.is_available():
            self.use_cuda_var.set(use_cuda.lower() == 'true')
        else:
            self.use_cuda_var.set(False)
            
        self.workers_var.set(int(workers))
        self._update_conf_label()

    def browse_model(self):
        path = filedialog.askopenfilename(filetypes=[("YOLO Model", "*.pt")])
        if path:
            self.model_path_var.set(path)

    def save_settings(self):
        self.settings.set_setting("auto_label_model", self.model_path_var.get())
        self.settings.set_setting("auto_label_confidence", self.conf_var.get())
        
        self.settings.set_setting("use_cuda_labeling", str(self.use_cuda_var.get()))
        self.settings.set_setting("labeling_workers", self.workers_var.get())
        self.destroy()
