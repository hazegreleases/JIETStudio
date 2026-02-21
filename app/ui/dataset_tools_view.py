import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import cv2
from PIL import Image
import threading
from app.ui.components import RoundedButton
from app.core.theme_manager import ThemeManager

class DatasetToolsView(tk.Frame):
    def __init__(self, parent, project_manager):
        super().__init__(parent)
        self.project_manager = project_manager
        self.theme = ThemeManager()
        self.configure(bg=self.theme.get("window_bg_color"))
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._create_stats_tab()
        self._create_health_tab()
        self._create_video_tab()
        self._create_export_tab()

    def _create_stats_tab(self):
        tab = tk.Frame(self.notebook, bg=self.theme.get("window_bg_color"))
        self.notebook.add(tab, text="Dataset Stats")
        
        tk.Label(tab, text="Class Distribution", font=("Arial", 12, "bold"), 
                 bg=self.theme.get("window_bg_color"), fg=self.theme.get("window_text_color")).pack(pady=10)
        
        self.stats_canvas = tk.Canvas(tab, bg="#1e1e1e", highlightthickness=0)
        self.stats_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        RoundedButton(tab, text="Refresh Stats", command=self.refresh_stats, width=120, height=35).pack(pady=10)
        
        # Initial refresh
        self.after(100, self.refresh_stats)

    def refresh_stats(self):
        self.stats_canvas.delete("all")
        w = self.stats_canvas.winfo_width()
        h = self.stats_canvas.winfo_height()
        if w < 10: return

        classes = self.project_manager.get_classes()
        counts = {cls: 0 for cls in classes}
        
        labels_dir = os.path.join(self.project_manager.current_project_path, "data", "labels")
        if not os.path.exists(labels_dir): return
        
        for f in os.listdir(labels_dir):
            if f.endswith(".txt"):
                path = os.path.join(labels_dir, f)
                with open(path, "r") as lf:
                    for line in lf:
                        parts = line.split()
                        if parts:
                            try:
                                idx = int(parts[0])
                                if idx < len(classes):
                                    counts[classes[idx]] += 1
                            except: pass
        
        if not counts or max(counts.values(), default=0) == 0:
            self.stats_canvas.create_text(w/2, h/2, text="No instances found.", fill="white")
            return

        max_val = max(counts.values())
        margin = 50
        bar_w = (w - 2*margin) / len(counts)
        chart_h = h - 2*margin
        
        for i, (cls, count) in enumerate(counts.items()):
            bar_h = (count / max_val) * chart_h
            x0 = margin + i * bar_w + 5
            y0 = h - margin - bar_h
            x1 = margin + (i+1) * bar_w - 5
            y1 = h - margin
            
            # Draw bar
            self.stats_canvas.create_rectangle(x0, y0, x1, y1, fill="#4a90e2", outline="")
            # Label
            self.stats_canvas.create_text((x0+x1)/2, y1 + 15, text=cls, fill="white", font=("Arial", 8))
            # Count
            self.stats_canvas.create_text((x0+x1)/2, y0 - 10, text=str(count), fill="#aaa", font=("Arial", 8))

    def _create_health_tab(self):
        tab = tk.Frame(self.notebook, bg=self.theme.get("window_bg_color"))
        self.notebook.add(tab, text="Health Check")
        
        btn_frame = tk.Frame(tab, bg=self.theme.get("window_bg_color"))
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        RoundedButton(btn_frame, text="Run Health Scan", command=self.run_health_check, width=150, height=35).pack(side=tk.LEFT)
        
        self.health_log = tk.Text(tab, bg="black", fg="#00ff00", font=("Consolas", 10))
        self.health_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def run_health_check(self):
        self.health_log.delete("1.0", tk.END)
        self.health_log.insert(tk.END, "Starting Dataset Health Scan...\n")
        
        images_dir = os.path.join(self.project_manager.current_project_path, "data", "images")
        labels_dir = os.path.join(self.project_manager.current_project_path, "data", "labels")
        classes = self.project_manager.get_classes()
        
        issues = 0
        img_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        self.health_log.insert(tk.END, f"Checking {len(img_files)} images...\n")
        
        for f in img_files:
            img_path = os.path.join(images_dir, f)
            label_path = os.path.join(labels_dir, os.path.splitext(f)[0] + ".txt")
            
            # 1. Corrupted image check
            try:
                with Image.open(img_path) as img:
                    img.verify()
            except Exception as e:
                self.health_log.insert(tk.END, f"[ERROR] Corrupted image: {f} - {e}\n", "err")
                issues += 1
                continue
            
            # 2. Missing label check
            if not os.path.exists(label_path):
                self.health_log.insert(tk.END, f"[WARN] Missing label file: {f} (Will be ignored in training)\n", "warn")
                issues += 1
                continue
            
            # 3. Label content check
            with open(label_path, "r") as lf:
                lines = lf.readlines()
                for i, line in enumerate(lines):
                    parts = line.split()
                    if len(parts) != 5:
                        self.health_log.insert(tk.END, f"[ERROR] Bad label format {f} line {i+1}\n")
                        issues += 1
                        continue
                    
                    try:
                        cls_id, cx, cy, bw, bh = map(float, parts)
                        if cls_id >= len(classes):
                            self.health_log.insert(tk.END, f"[ERROR] Invalid class ID {int(cls_id)} in {f}\n")
                            issues += 1
                        if cx < 0 or cx > 1 or cy < 0 or cy > 1 or bw < 0 or bw > 1 or bh < 0 or bh > 1:
                            self.health_log.insert(tk.END, f"[WARN] Out of bounds box in {f}\n")
                            issues += 1
                    except:
                        self.health_log.insert(tk.END, f"[ERROR] Non-numeric data in {f}\n")
                        issues += 1

        self.health_log.insert(tk.END, f"\nScan complete. Found {issues} potential issues.\n")
        self.health_log.tag_config("err", foreground="red")
        self.health_log.tag_config("warn", foreground="orange")

    def _create_video_tab(self):
        tab = tk.Frame(self.notebook, bg=self.theme.get("window_bg_color"))
        self.notebook.add(tab, text="Video Extraction")
        
        fields = tk.Frame(tab, bg=self.theme.get("window_bg_color"), padx=20, pady=20)
        fields.pack(fill=tk.X)
        
        tk.Label(fields, text="Source Video:", bg=self.theme.get("window_bg_color"), fg="white").grid(row=0, column=0, sticky=tk.W)
        self.video_path_var = tk.StringVar()
        tk.Entry(fields, textvariable=self.video_path_var, width=50, bg="#333", fg="white", insertbackground="white").grid(row=0, column=1, padx=5)
        RoundedButton(fields, text="Browse", command=self.browse_video, width=80, height=25).grid(row=0, column=2)
        
        tk.Label(fields, text="Extract Every Nth Frame:", bg=self.theme.get("window_bg_color"), fg="white").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.frame_step_var = tk.IntVar(value=30)
        tk.Entry(fields, textvariable=self.frame_step_var, width=10, bg="#333", fg="white", insertbackground="white").grid(row=1, column=1, sticky=tk.W, padx=5)
        
        self.extract_btn = RoundedButton(tab, text="Start Extraction", command=self.start_video_extraction, width=180, height=40)
        self.extract_btn.pack(pady=10)
        
        self.video_log = tk.Label(tab, text="Ready", bg=self.theme.get("window_bg_color"), fg="#aaa")
        self.video_log.pack()

    def browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            self.video_path_var.set(path)

    def start_video_extraction(self):
        video_path = self.video_path_var.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "Select a valid video file")
            return
            
        step = self.frame_step_var.get()
        if step < 1: step = 1
        
        self.extract_btn.config(state="disabled")
        threading.Thread(target=self._extract_thread, args=(video_path, step), daemon=True).start()

    def _extract_thread(self, path, step):
        try:
            cap = cv2.VideoCapture(path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            count = 0
            saved = 0
            
            output_dir = os.path.join(self.project_manager.current_project_path, "data", "images")
            prefix = os.path.splitext(os.path.basename(path))[0]
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                if count % step == 0:
                    out_name = f"{prefix}_frame_{count:06d}.jpg"
                    out_path = os.path.join(output_dir, out_name)
                    cv2.imwrite(out_path, frame)
                    saved += 1
                    self.video_log.config(text=f"Progress: {count}/{total} frames ({saved} saved)")
                
                count += 1
            
            cap.release()
            messagebox.showinfo("Success", f"Extracted {saved} frames to project images folder.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.extract_btn.config(state="normal")
            self.video_log.config(text="Ready")

    def _create_export_tab(self):
        tab = tk.Frame(self.notebook, bg=self.theme.get("window_bg_color"))
        self.notebook.add(tab, text="Export Project")
        
        content = tk.Frame(tab, bg=self.theme.get("window_bg_color"), padx=40, pady=40)
        content.pack(expand=True)
        
        tk.Label(content, text="Project Zipping", font=("Arial", 14, "bold"), 
                 bg=self.theme.get("window_bg_color"), fg="white").pack(pady=10)
        
        tk.Label(content, text="Compress the entire project folder (images, labels, configs, results)\ninto a single ZIP file for sharing or backup.", 
                 bg=self.theme.get("window_bg_color"), fg="#aaa", justify=tk.CENTER).pack(pady=10)
        
        RoundedButton(content, text="Export Project as ZIP", command=self.export_zip, width=220, height=50).pack(pady=20)

    def export_zip(self):
        project_path = self.project_manager.current_project_path
        project_name = os.path.basename(project_path)
        
        save_path = filedialog.asksaveasfilename(defaultextension=".zip", 
                                                 initialfile=f"{project_name}_backup.zip",
                                                 filetypes=[("ZIP files", "*.zip")])
        if not save_path: return
        
        try:
            # shutil.make_archive takes base_name without extension, and appends it.
            # But asksaveasfilename might have added .zip already.
            base_name = os.path.splitext(save_path)[0]
            
            self.after(0, lambda: messagebox.showinfo("Exporting", "Zipping project... This may take a while for large datasets."))
            
            def run_zip():
                shutil.make_archive(base_name, 'zip', project_path)
                self.after(0, lambda: messagebox.showinfo("Success", f"Project exported to:\n{save_path}"))
                
            threading.Thread(target=run_zip, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export ZIP: {e}")
