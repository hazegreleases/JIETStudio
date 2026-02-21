import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from app.ui.components import RoundedButton
from PIL import Image, ImageTk
import cv2
import threading
import os

class InferenceView(tk.Frame):
    def __init__(self, parent, project_manager):
        super().__init__(parent)
        self.project_manager = project_manager
        # We instantiate wrapper here too, or pass it in. 
        # Since wrapper takes project path, we can create new one.
        from app.core.yolo_wrapper import YOLOWrapper
        self.yolo_wrapper = YOLOWrapper(project_manager.current_project_path)
        
        self.cap = None
        self.is_running = False
        self.current_image = None
        
        self._create_ui()

    def _create_ui(self):
        # Control Panel
        control_frame = tk.Frame(self, padx=10, pady=10, bg="#ddd")
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Model Selection
        tk.Label(control_frame, text="Model Path:", bg="#ddd").grid(row=0, column=0, sticky=tk.W)
        self.model_path_var = tk.StringVar()
        tk.Entry(control_frame, textvariable=self.model_path_var, width=40).grid(row=0, column=1, padx=5)
        RoundedButton(control_frame, text="Browse", command=self.browse_model, width=80, height=30).grid(row=0, column=2, padx=5)

        # Source Selection
        tk.Label(control_frame, text="Source:", bg="#ddd").grid(row=1, column=0, sticky=tk.W)
        self.source_var = tk.StringVar(value="Image")
        ttk.Combobox(control_frame, textvariable=self.source_var, values=["Image", "Video File", "Batch Folder", "Webcam 0", "Webcam 1"]).grid(row=1, column=1, padx=5, sticky=tk.EW)
        
        self.run_btn = RoundedButton(control_frame, text="Run Inference", command=self.start_inference, width=120, height=30)
        self.run_btn.grid(row=1, column=2, padx=5)
        
        self.stop_btn = RoundedButton(control_frame, text="Stop Inference", command=self.stop_inference, width=120, height=30)
        self.stop_btn.grid(row=1, column=3, padx=5)
        self.stop_btn.config(state="disabled")

        # Export
        tk.Label(control_frame, text="Export:", bg="#ddd").grid(row=0, column=3, sticky=tk.W, padx=(20, 5))
        RoundedButton(control_frame, text="Export ONNX", command=lambda: self.export_model("onnx"), width=120, height=30).grid(row=0, column=4, padx=2)
        RoundedButton(control_frame, text="Export TorchScript", command=lambda: self.export_model("torchscript"), width=150, height=30).grid(row=0, column=5, padx=2)

        # Display Area
        self.display_frame = tk.Frame(self, bg="black")
        self.display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.display_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def browse_model(self):
        # Default to runs directory if exists
        initial_dir = os.path.join(self.project_manager.current_project_path, "runs")
        if not os.path.exists(initial_dir):
            initial_dir = self.project_manager.current_project_path
            
        path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Model Files", "*.pt")])
        if path:
            self.model_path_var.set(path)
            
    def update_buttons(self, running):
        if running:
            self.run_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        else:
            self.run_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def start_inference(self):
        model_path = self.model_path_var.get()
        if not model_path or not os.path.exists(model_path):
            messagebox.showerror("Error", "Invalid model path")
            return

        source = self.source_var.get()
        
        if source == "Image":
            file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
            if not file_path: return
            
            self.run_image_inference(model_path, file_path)
        
        elif source == "Video File":
            file_path = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.avi *.mov")])
            if not file_path: return
            self.run_video_inference(model_path, file_path)
            self.update_buttons(True)
            
        elif source == "Batch Folder":
            dir_path = filedialog.askdirectory()
            if not dir_path: return
            self.run_batch_inference(model_path, dir_path)
            self.update_buttons(True)
            
        elif "Webcam" in source:
            cam_idx = int(source.split()[-1])
            self.run_webcam_inference(model_path, cam_idx)
            self.update_buttons(True)

    def run_image_inference(self, model_path, image_path):
        try:
            results = self.yolo_wrapper.run_inference(model_path, image_path)
            # Results is a list
            for r in results:
                im_array = r.plot()  # plot() returns BGR numpy array
                im_rgb = cv2.cvtColor(im_array, cv2.COLOR_BGR2RGB)
                self.display_image(im_rgb)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_webcam_inference(self, model_path, cam_idx):
        self.cap = cv2.VideoCapture(cam_idx)
        if not self.cap.isOpened():
            messagebox.showerror("Error", f"Cannot open webcam {cam_idx}")
            return
            
        self.is_running = True
        
        def loop():
            from ultralytics import YOLO
            model = YOLO(model_path)
            
            while self.is_running and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret: break
                
                results = model.predict(frame, conf=0.5, verbose=False)
                annotated_frame = results[0].plot()
                
                im_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                
                # Schedule update on main thread
                self.after(10, lambda img=im_rgb: self.display_image(img))
            
            self.cap.release()
            self.canvas.delete("all")
            self.after(0, lambda: self.update_buttons(False))

        threading.Thread(target=loop, daemon=True).start()

    def run_video_inference(self, model_path, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.is_running = True
        
        def loop():
            from ultralytics import YOLO
            model = YOLO(model_path)
            while self.is_running and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret: break
                
                results = model.predict(frame, conf=0.5, verbose=False)
                annotated_frame = results[0].plot()
                im_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                self.after(1, lambda img=im_rgb: self.display_image(img))
            
            self.cap.release()
            self.after(0, lambda: self.update_buttons(False))

        threading.Thread(target=loop, daemon=True).start()

    def run_batch_inference(self, model_path, folder_path):
        self.is_running = True
        
        def loop():
            from ultralytics import YOLO
            import time
            model = YOLO(model_path)
            
            output_dir = os.path.join(folder_path, "inference_results")
            os.makedirs(output_dir, exist_ok=True)
            
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            for i, f in enumerate(files):
                if not self.is_running: break
                
                img_path = os.path.join(folder_path, f)
                results = model.predict(img_path, conf=0.5, verbose=False)
                
                # Save result
                res_img = results[0].plot()
                cv2.imwrite(os.path.join(output_dir, f), res_img)
                
                # Update UI
                im_rgb = cv2.cvtColor(res_img, cv2.COLOR_BGR2RGB)
                self.after(0, lambda img=im_rgb: self.display_image(img))
            
            self.is_running = False
            self.after(0, lambda: self.update_buttons(False))
            self.after(0, lambda: messagebox.showinfo("Batch Complete", f"Processed {len(files)} images.\nResults saved to {output_dir}"))

        threading.Thread(target=loop, daemon=True).start()

    def stop_inference(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.update_buttons(False)

    def display_image(self, bgr_img):
        # bgr_img can be numpy array
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10 or ch < 10: return
        
        # Determine aspect ratio preserving scale
        ih, iw = bgr_img.shape[:2]
        scale = min(cw / iw, ch / ih)
        new_w, new_h = int(iw * scale), int(ih * scale)
        
        resized = cv2.resize(bgr_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        self.img_tk = ImageTk.PhotoImage(image=im)
        self.canvas.delete("all")
        self.canvas.create_image(cw//2, ch//2, anchor=tk.CENTER, image=self.img_tk)

    def export_model(self, fmt):
        model_path = self.model_path_var.get()
        if not model_path or not os.path.exists(model_path):
            messagebox.showerror("Error", "Invalid model path")
            return
            
        try:
            export_path = self.yolo_wrapper.export_model(model_path, fmt)
            messagebox.showinfo("Success", f"Model exported to {export_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
