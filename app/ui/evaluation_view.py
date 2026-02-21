import tkinter as tk
from tkinter import ttk, messagebox
import os
import cv2
from PIL import Image, ImageTk
from app.ui.components import RoundedButton
from app.core.theme_manager import ThemeManager

class EvaluationView(tk.Frame):
    def __init__(self, parent, project_manager):
        super().__init__(parent)
        self.project_manager = project_manager
        self.theme = ThemeManager()
        self.configure(bg=self.theme.get("window_bg_color"))
        
        self.runs_dir = os.path.join(project_manager.current_project_path, "runs")
        self.current_run = None
        self.val_images = []
        self.current_val_idx = 0
        
        self._create_ui()

    def _create_ui(self):
        # Run Selector
        select_frame = tk.Frame(self, bg=self.theme.get("window_bg_color"), pady=10)
        select_frame.pack(fill=tk.X)
        
        tk.Label(select_frame, text="Select Run:", bg=self.theme.get("window_bg_color"), fg="white").pack(side=tk.LEFT, padx=10)
        
        self.run_var = tk.StringVar()
        self.run_combo = ttk.Combobox(select_frame, textvariable=self.run_var, width=30)
        self.run_combo.pack(side=tk.LEFT, padx=5)
        self.run_combo.bind("<<ComboboxSelected>>", self.on_run_selected)
        
        RoundedButton(select_frame, text="Refresh Runs", command=self.refresh_runs, width=120, height=30).pack(side=tk.LEFT, padx=10)
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.refresh_runs()

    def refresh_runs(self):
        if not os.path.exists(self.runs_dir):
            return
        
        runs = [d for d in os.listdir(self.runs_dir) if (d.startswith("train") or d.startswith("val")) and os.path.isdir(os.path.join(self.runs_dir, d))]
        # Sort by mtime
        runs.sort(key=lambda x: os.path.getmtime(os.path.join(self.runs_dir, x)), reverse=True)
        
        self.run_combo['values'] = runs
        if runs:
            self.run_combo.current(0)
            self.on_run_selected(None)

    def on_run_selected(self, event):
        self.current_run = self.run_var.get()
        self._update_tabs()

    def _update_tabs(self):
        # Clear tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
            
        self._create_metrics_tab()
        self._create_comparison_tab()

    def _create_metrics_tab(self):
        tab = tk.Frame(self.notebook, bg=self.theme.get("window_bg_color"))
        self.notebook.add(tab, text="Metrics Dashboard")
        
        self.metrics_container = tk.PanedWindow(tab, orient=tk.HORIZONTAL, bg=self.theme.get("window_bg_color"), sashwidth=4)
        self.metrics_container.pack(fill=tk.BOTH, expand=True)
        
        run_path = os.path.join(self.runs_dir, self.current_run)
        
        self._add_metric_view(self.metrics_container, os.path.join(run_path, "results.png"), "Training Progress (Results.png)")
        self._add_metric_view(self.metrics_container, os.path.join(run_path, "confusion_matrix.png"), "Confusion Matrix")
        
        # Force 50/50 split after layout
        self.after(500, lambda: self.metrics_container.sash_place(0, self.winfo_width()//2, 0))

    def _add_metric_view(self, parent, path, title):
        child = tk.Frame(parent, bg=self.theme.get("window_bg_color"))
        parent.add(child)
        
        tk.Label(child, text=title, bg=self.theme.get("window_bg_color"), fg="white").pack(pady=5)
        canvas = tk.Canvas(child, bg="#111", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        if os.path.exists(path):
            self.after(200, lambda: self._draw_img_on_canvas(canvas, path))
        else:
            canvas.create_text(150, 100, text="Metric file not found in this run.", fill="#555")

    def _draw_img_on_canvas(self, canvas, path):
        try:
            img = Image.open(path)
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            if cw < 10 or ch < 10: 
                self.after(200, lambda: self._draw_img_on_canvas(canvas, path))
                return
            
            # FIT logic: Scale to fill max available space while preserving aspect
            img_w, img_h = img.size
            scale = min(cw / img_w, ch / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            canvas.image = photo 
            canvas.delete("all")
            canvas.create_image(cw//2, ch//2, anchor=tk.CENTER, image=photo)
        except: pass

    def _create_comparison_tab(self):
        tab = tk.Frame(self.notebook, bg=self.theme.get("window_bg_color"))
        self.notebook.add(tab, text="Visual Evaluation (GT vs Pred)")
        
        # Load val images from val.txt if exists
        val_txt = os.path.join(self.project_manager.current_project_path, "data", "val.txt")
        if os.path.exists(val_txt):
            with open(val_txt, "r") as f:
                self.val_images = [line.strip() for line in f if line.strip()]
        
        if not self.val_images:
            tk.Label(tab, text="No validation images found. Run a training session first.", 
                     bg=self.theme.get("window_bg_color"), fg="white").pack(pady=50)
            return

        ctrl_frame = tk.Frame(tab, bg=self.theme.get("window_bg_color"))
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        RoundedButton(ctrl_frame, text="<< Prev", command=self.prev_val, width=80, height=30).pack(side=tk.LEFT, padx=5)
        self.val_lbl = tk.Label(ctrl_frame, text=f"Image 1 / {len(self.val_images)}", bg=self.theme.get("window_bg_color"), fg="white")
        self.val_lbl.pack(side=tk.LEFT, padx=20)
        RoundedButton(ctrl_frame, text="Next >>", command=self.next_val, width=80, height=30).pack(side=tk.LEFT, padx=5)
        
        # Split view
        self.comp_paned = tk.PanedWindow(tab, orient=tk.HORIZONTAL, bg=self.theme.get("window_bg_color"), sashwidth=4)
        self.comp_paned.pack(fill=tk.BOTH, expand=True)
        
        self.gt_canvas = tk.Canvas(self.comp_paned, bg="black", highlightthickness=0)
        self.pred_canvas = tk.Canvas(self.comp_paned, bg="black", highlightthickness=0)
        
        self.comp_paned.add(self.gt_canvas)
        self.comp_paned.add(self.pred_canvas)
        
        # Force 50/50 split after layout
        self.after(500, lambda: self.comp_paned.sash_place(0, self.winfo_width()//2, 0))
        
        tk.Label(self.gt_canvas, text="GROUND TRUTH", bg="black", fg="#00ff00").place(x=10, y=10)
        tk.Label(self.pred_canvas, text="MODEL PREDICTION", bg="black", fg="#4a90e2").place(x=10, y=10)
        
        self.after(200, self.update_comparison)

    def prev_val(self):
        if self.current_val_idx > 0:
            self.current_val_idx -= 1
            self.update_comparison()

    def next_val(self):
        if self.current_val_idx < len(self.val_images) - 1:
            self.current_val_idx += 1
            self.update_comparison()

    def update_comparison(self):
        if not self.val_images: return
        img_path = self.val_images[self.current_val_idx]
        self.val_lbl.config(text=f"Image {self.current_val_idx + 1} / {len(self.val_images)}: {os.path.basename(img_path)}")
        
        # Load GT
        self._draw_gt(img_path)
        # Load Pred
        self._draw_pred(img_path)

    def _draw_gt(self, img_path):
        try:
            img = cv2.imread(img_path)
            h, w, _ = img.shape
            label_path = os.path.join(self.project_manager.current_project_path, "data", "labels", os.path.splitext(os.path.basename(img_path))[0] + ".txt")
            classes = self.project_manager.get_classes()
            
            if os.path.exists(label_path):
                with open(label_path, "r") as f:
                    for line in f:
                        cls_idx, cx, cy, bw, bh = map(float, line.split())
                        x1 = int((cx - bw/2) * w)
                        y1 = int((cy - bh/2) * h)
                        x2 = int((cx + bw/2) * w)
                        y2 = int((cy + bh/2) * h)
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cls_name = classes[int(cls_idx)] if int(cls_idx) < len(classes) else str(int(cls_idx))
                        cv2.putText(img, cls_name, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            self._display_on_canvas(self.gt_canvas, img)
        except: pass

    def _draw_pred(self, img_path):
        try:
            # Need model path
            model_path = os.path.join(self.runs_dir, self.current_run, "weights", "best.pt")
            if not os.path.exists(model_path):
                # fallback to last.pt
                model_path = os.path.join(self.runs_dir, self.current_run, "weights", "last.pt")
            
            if not os.path.exists(model_path):
                return
            
            from ultralytics import YOLO
            model = YOLO(model_path)
            results = model.predict(img_path, conf=0.25, verbose=False)
            res_img = results[0].plot() # returns BGR
            
            self._display_on_canvas(self.pred_canvas, res_img)
        except: pass

    def _display_on_canvas(self, canvas, bgr_img):
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 10 or ch < 10: return
        
        rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        
        # FIT logic: Scale to fill max available space while preserving aspect
        img_w, img_h = pil_img.size
        scale = min(cw / img_w, ch / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        
        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(pil_img)
        if not hasattr(canvas, 'images'): canvas.images = []
        canvas.images.append(photo) # keep reference
        if len(canvas.images) > 2: canvas.images.pop(0) 
        
        canvas.delete("all")
        canvas.create_image(cw//2, ch//2, anchor=tk.CENTER, image=photo)
