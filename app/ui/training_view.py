import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app.core.yolo_wrapper import YOLOWrapper
from app.ui.components import RoundedButton
import sys
import os

import re

class RedirectText(object):
    def __init__(self, text_widget, callback=None):
        self.output = text_widget
        self.callback = callback

    def write(self, string):
        try:
            # Detect \r (tqdm-style progress updates)
            if '\r' in string:
                last_part = string.split('\r')[-1]
                if self.callback:
                    self.callback(last_part)
            
            self.output.insert(tk.END, string)
            self.output.see(tk.END)
            
            if '\n' in string and self.callback:
                for line in string.splitlines():
                    self.callback(line)
        except tk.TclError:
            pass

    def flush(self):
        pass

class TrainingView(tk.Frame):
    def __init__(self, parent, project_manager, unload_callback=None, reload_callback=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.yolo_wrapper = YOLOWrapper(project_manager.current_project_path)
        
        # Model management callbacks
        self.unload_models_callback = unload_callback
        self.reload_models_callback = reload_callback
        
        # Store original stdout/stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        self._create_ui()
        
        # Redirect stdout/stderr
        sys.stdout = RedirectText(self.console_text, callback=self.parse_progress)
        sys.stderr = RedirectText(self.console_text, callback=self.parse_progress)

    def _create_ui(self):
        # Create Notebook for Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Config Panel (Tab 1)
        config_frame = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(config_frame, text="Basic Settings")
        
        # Hyperparameters (Tab 2)
        self.hyper_frame = tk.Frame(self.notebook, padx=10, pady=10)
        self.notebook.add(self.hyper_frame, text="Hyperparameters")
        self._create_hyperparams_ui()

        # Model Selection
        tk.Label(config_frame, text="Model:").grid(row=0, column=0, sticky=tk.W)
        self.model_var = tk.StringVar(value="yolov8n.pt")
        models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt",
                  "yolo11n.pt", "yolo11s.pt", "yolo11m.pt", "yolo11l.pt", "yolo11x.pt",
                  "yolo26n.pt", "yolo26s.pt", "yolo26m.pt", "yolo26l.pt", "yolo26x.pt"]
        self.model_combo = ttk.Combobox(config_frame, textvariable=self.model_var, values=models)
        self.model_combo.grid(row=0, column=1, padx=5, pady=5)
        
        RoundedButton(config_frame, text="Import Model", command=self.import_model, width=120, height=30).grid(row=0, column=2, padx=5)
        
        self.pretrained_var = tk.BooleanVar(value=True)
        tk.Checkbutton(config_frame, text="Pretrained", variable=self.pretrained_var).grid(row=0, column=3)
        
        self.resume_var = tk.BooleanVar(value=False)
        tk.Checkbutton(config_frame, text="Resume Training", variable=self.resume_var).grid(row=0, column=4, sticky=tk.W)

        # Parameters
        tk.Label(config_frame, text="Epochs:").grid(row=1, column=0, sticky=tk.W)
        self.epochs_var = tk.IntVar(value=50)
        tk.Entry(config_frame, textvariable=self.epochs_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(config_frame, text="Batch Size:").grid(row=1, column=2, sticky=tk.W)
        self.batch_var = tk.IntVar(value=16)
        tk.Entry(config_frame, textvariable=self.batch_var, width=10).grid(row=1, column=3, padx=5, pady=5)

        tk.Label(config_frame, text="Image Size:").grid(row=1, column=4, sticky=tk.W)
        self.imgsz_var = tk.IntVar(value=640)
        tk.Entry(config_frame, textvariable=self.imgsz_var, width=10).grid(row=1, column=5, padx=5, pady=5)

        # Validation Split
        tk.Label(config_frame, text="Val Split (%):").grid(row=2, column=0, sticky=tk.W)
        self.val_split_var = tk.IntVar(value=20)
        self.val_slider = tk.Scale(config_frame, from_=0, to=50, orient=tk.HORIZONTAL, variable=self.val_split_var)
        self.val_slider.grid(row=2, column=1, columnspan=2, sticky=tk.EW)

        # Background Ratio
        tk.Label(config_frame, text="BG Ratio (%):").grid(row=2, column=3, sticky=tk.W, padx=(10, 0))
        self.bg_ratio_var = tk.IntVar(value=10)
        self.bg_slider = tk.Scale(config_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.bg_ratio_var)
        self.bg_slider.grid(row=2, column=4, columnspan=2, sticky=tk.EW)


        # Advanced Settings (Half, Workers)
        tk.Label(config_frame, text="Workers:").grid(row=3, column=0, sticky=tk.W)
        self.workers_var = tk.IntVar(value=max(1, (os.cpu_count() or 4) // 2))
        tk.Entry(config_frame, textvariable=self.workers_var, width=10).grid(row=3, column=1, padx=5, pady=5)
        
        self.half_var = tk.BooleanVar(value=False)
        # Default half to False usually, but maybe True if CUDA? 
        # User requested: "one bieng a boolean for half=true/false, it shuld write half(fp16) in the tab"
        tk.Checkbutton(config_frame, text="half (fp16)", variable=self.half_var).grid(row=3, column=2, sticky=tk.W)

        # Train Button
        # We need to wrap RoundedButton in a frame or use place if grid is tricky with canvas size, 
        # but grid works fine for canvas.
        self.start_btn = RoundedButton(config_frame, text="START TRAINING", command=self.start_training, 
                                  width=200, height=50)
        self.start_btn.grid(row=4, column=0, columnspan=3, pady=20, sticky=tk.E, padx=5)

        self.stop_btn = RoundedButton(config_frame, text="STOP TRAINING", command=self.stop_training, 
                                  width=200, height=50)
        self.stop_btn.grid(row=4, column=3, columnspan=3, pady=20, sticky=tk.W, padx=5)
        self.stop_btn.config(state="disabled")

        # Console Output
        tk.Label(self, text="Training Log:").pack(anchor=tk.W, padx=10)
        
        # Resource Monitor Bar
        self.resource_frame = tk.Frame(self, bg="#222")
        self.resource_frame.pack(fill=tk.X, padx=10, pady=2)
        
        self.lbl_device = tk.Label(self.resource_frame, text="Device: Detecting...", bg="#222", fg="#aaa", font=("Consolas", 9))
        self.lbl_device.pack(side=tk.LEFT, padx=5)
        
        self.lbl_cpu = tk.Label(self.resource_frame, text="CPU: 0%", bg="#222", fg="#aaa", font=("Consolas", 9))
        self.lbl_cpu.pack(side=tk.RIGHT, padx=5)
        
        self.lbl_ram = tk.Label(self.resource_frame, text="RAM: 0%", bg="#222", fg="#aaa", font=("Consolas", 9))
        self.lbl_ram.pack(side=tk.RIGHT, padx=5)

        self.lbl_gpu = tk.Label(self.resource_frame, text="GPU: N/A", bg="#222", fg="#aaa", font=("Consolas", 9))
        self.lbl_gpu.pack(side=tk.RIGHT, padx=5)

        # CUDA Status
        cuda_status = "CUDA: Unavailable"
        cuda_color = "red"
        try:
            import torch
            if torch.cuda.is_available():
                cuda_status = "CUDA: Installed"
                cuda_color = "#00ff00" # Bright green
        except ImportError:
            pass

        self.lbl_cuda = tk.Label(self.resource_frame, text=cuda_status, bg="#222", fg=cuda_color, font=("Consolas", 9, "bold"))
        self.lbl_cuda.pack(side=tk.RIGHT, padx=10)

        # Progress info
        self.lbl_epoch = tk.Label(self.resource_frame, text="Epoch: -/-", bg="#222", fg="#00ff00", font=("Consolas", 9, "bold"))
        self.lbl_epoch.pack(side=tk.LEFT, padx=10)

        self.lbl_progress = tk.Label(self.resource_frame, text="Progress: 0%", bg="#222", fg="#00ff00", font=("Consolas", 9, "bold"))
        self.lbl_progress.pack(side=tk.LEFT, padx=10)

        self.lbl_eta = tk.Label(self.resource_frame, text="ETA: --:--", bg="#222", fg="#aaa", font=("Consolas", 9))
        self.lbl_eta.pack(side=tk.LEFT, padx=5)

        self.console_text = tk.Text(self, bg="black", fg="white", height=20)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.monitor = None
        self.start_monitoring()

    def _create_hyperparams_ui(self):
        self.hyper_vars = {}
        
        params = [
            ("Initial Learning Rate (lr0)", "lr0", 0.01),
            ("Final Learning Rate (lrf)", "lrf", 0.01),
            ("Momentum", "momentum", 0.937),
            ("Weight Decay", "weight_decay", 0.0005),
            ("Warmup Epochs", "warmup_epochs", 3.0),
            ("Warmup Momentum", "warmup_momentum", 0.8),
            ("Box Loss Gain", "box", 7.5),
            ("Cls Loss Gain", "cls", 0.5),
            ("DFL Loss Gain", "dfl", 1.5),
            ("Mosaic (0.0-1.0)", "mosaic", 1.0),
            ("Mixup (0.0-1.0)", "mixup", 0.0),
        ]
        
        row = 0
        col = 0
        for label, name, default in params:
            tk.Label(self.hyper_frame, text=label + ":").grid(row=row, column=col*2, sticky=tk.W, padx=5, pady=5)
            var = tk.DoubleVar(value=default)
            self.hyper_vars[name] = var
            tk.Entry(self.hyper_frame, textvariable=var, width=10).grid(row=row, column=col*2+1, padx=5, pady=5)
            
            row += 1
            if row > 4:
                row = 0
                col += 1

    def start_monitoring(self):
        from app.core.resource_monitor import ResourceMonitor
        self.monitor = ResourceMonitor(callback=self.update_stats)
        self.monitor.start()
        
        # Update device info
        device_info = self.yolo_wrapper.get_device_info()
        self.lbl_device.config(text=f"Device: {device_info}")

    def parse_progress(self, line):
        """Parse YOLO tqdm output for epoch, progress % and ETA."""
        if not line or not self.winfo_exists():
            return
            
        # Example: " 1/50   14.7G   0.123 ... 10/10 [00:05<00:00,  1.92it/s]"
        epoch_match = re.search(r'(\d+)/(\d+)', line)
        if epoch_match:
            curr, total = epoch_match.groups()
            # Heuristic: if total is high, it's likely the epoch count
            try:
                if int(total) >= self.epochs_var.get():
                    self.lbl_epoch.config(text=f"Epoch: {curr}/{total}")
            except: pass
            
        percent_match = re.search(r'(\d+)%', line)
        if percent_match:
            self.lbl_progress.config(text=f"Progress: {percent_match.group(1)}%")
            
        eta_match = re.search(r'<(\d+:\d+)', line)
        if eta_match:
            self.lbl_eta.config(text=f"ETA: {eta_match.group(1)}")

    def update_stats(self, stats):
        if not self.winfo_exists():
            return
            
        # Schedule UI update on main thread
        self.after(0, lambda: self._update_labels(stats))

    def _update_labels(self, stats):
        self.lbl_cpu.config(text=f"CPU: {stats['cpu']}%")
        self.lbl_ram.config(text=f"RAM: {stats['ram']}%")
        self.lbl_gpu.config(text=f"GPU: {stats['gpu']}")

    def import_model(self):
        path = filedialog.askopenfilename(filetypes=[("Model Files", "*.pt *.onnx")])
        if path:
            self.model_var.set(path)

    def start_training(self):
        try:
            epochs = self.epochs_var.get()
            batch = self.batch_var.get()
            imgsz = self.imgsz_var.get()
            bg_ratio = self.bg_ratio_var.get() / 100.0
            resume = self.resume_var.get()
            
            classes = self.project_manager.get_classes()
            if not classes:
                messagebox.showerror("Error", "No classes defined! Please add classes in Labeling tab.")
                return
            
            # Unload background models to free memory
            if self.unload_models_callback:
                self.unload_models_callback()

            # Gather hyperparameters
            hyperparams = {k: v.get() for k, v in self.hyper_vars.items()}

            self.console_text.insert(tk.END, f"Preparing dataset (BG Ratio: {bg_ratio:.1%})...\n")
            train_txt, val_txt = self.yolo_wrapper.prepare_dataset(self.val_split_var.get(), bg_ratio=bg_ratio)
            
            self.console_text.insert(tk.END, "Generating config...\n")
            data_yaml = self.yolo_wrapper.generate_yaml(classes, train_txt, val_txt)
            
            self.console_text.insert(tk.END, f"Starting training with {self.model_var.get()} (Resume: {resume})...\n")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.yolo_wrapper.train_model(self.model_var.get(), data_yaml, epochs, batch, imgsz, 
                                          callback=self.on_training_complete, half=self.half_var.get(), 
                                          workers=self.workers_var.get(), resume=resume, **hyperparams)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def stop_training(self):
        if messagebox.askyesno("Stop Training", "Are you sure you want to stop training? It will stop after the current epoch."):
            self.yolo_wrapper.stop_training()
            self.console_text.insert(tk.END, "Stopping training... (waiting for epoch end)\n")
            self.stop_btn.config(state="disabled") # Prevent multiple clicks

    def on_training_complete(self, message):
        try:
            self.console_text.insert(tk.END, f"\n{message}\n")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            
            # Reload background models
            if self.reload_models_callback:
                self.reload_models_callback()
            
            messagebox.showinfo("Training", "Training process finished.")
        except tk.TclError:
            pass

    def destroy(self):
        if self.monitor:
            self.monitor.stop()
        # Restore original stdout/stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        super().destroy()
