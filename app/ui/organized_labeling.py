import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from app.ui.components import RoundedButton
from PIL import Image, ImageTk
import os
import shutil
from app.core.theme_manager import ThemeManager
from datetime import datetime
from app.core.sam_wrapper import SAMWrapper

class OrganizedLabelingTool(ttk.Frame):
    """Tabbed labeling interface with drawing capabilities."""
    
    def __init__(self, parent, project_manager):
        super().__init__(parent)
        self.project_manager = project_manager
        self.theme = ThemeManager()
        
        # Drawing state
        self.current_image_path = None
        self.photo_image = None
        self.img_width = 0
        self.img_height = 0
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.pil_image = None  # Store original PIL image
        self.image_id = None
        
        self.boxes = []  # {'id': rect_id, 'text_id': text_id, 'class': class_name, 'bbox': [x1,y1,x2,y2]}
        self.current_box_start = None
        self.drawing_rect_id = None
        self.selected_class = None
        
        # Crosshair guides
        self.crosshair_x = None
        self.crosshair_y = None
        
        # History
        self.history = []
        self.redo_stack = []
        
        # Auto-Label state
        # Model and confidence now in project_manager settings
        
        # SAM2 Magic Wand State
        self.sam_wrapper = None
        self.labeling_mode = "edit" # "edit", "draw", "magic"
        self.selected_box_idx = None
        
        # Track current selection context
        self.selected_image_for_deletion = None
        
        self.setup_ui()
        self.refresh_all_images()
    
    def setup_ui(self):
        # Main container - Three-pane horizontal layout
        self.main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=5)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 1. Left panel - Organized tabs
        left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(left_panel, minsize=150)
        
        # Import buttons in left panel
        import_frame = ttk.Frame(left_panel)
        import_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(import_frame, text="Import Images", command=self.import_images).pack(side=tk.LEFT, padx=2)
        ttk.Button(import_frame, text="Refresh", command=self.refresh_all_images).pack(side=tk.LEFT, padx=2)
        
        # Tab notebook
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.classes_tab = self.create_classes_tab()
        self.unlabeled_tab = self.create_simple_tab("Unlabeled")
        self.verified_bg_tab = self.create_simple_tab("Verified BG")
        self.notebook.add(self.classes_tab, text="Classes")
        self.notebook.add(self.unlabeled_tab, text="Unlabeled")
        self.notebook.add(self.verified_bg_tab, text="Verified BG")
        
        # 2. Middle panel - Tools + Canvas
        middle_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(middle_panel, minsize=400)
        
        # Tools frame
        tools_frame = ttk.Frame(middle_panel)
        tools_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Mode Selection Buttons
        self.btn_edit = RoundedButton(tools_frame, text="Edit (1)", command=lambda: self.set_mode("edit"), 
                                      width=80, height=30, font=(self.theme.get("font_family"), 10))
        self.btn_edit.pack(side=tk.LEFT, padx=2)
        
        self.btn_draw = RoundedButton(tools_frame, text="Draw (2)", command=lambda: self.set_mode("draw"), 
                                      width=80, height=30, font=(self.theme.get("font_family"), 10))
        self.btn_draw.pack(side=tk.LEFT, padx=2)
        
        self.btn_magic = RoundedButton(tools_frame, text="Magic (3)", command=lambda: self.set_mode("magic"), 
                                     width=80, height=30, font=(self.theme.get("font_family"), 10))
        self.btn_magic.pack(side=tk.LEFT, padx=2)

        ttk.Label(tools_frame, text="Brush:").pack(side=tk.LEFT, padx=(10, 5))
        
        # Class selector (brush)
        self.class_var = tk.StringVar()
        self.class_combo = ttk.Combobox(tools_frame, textvariable=self.class_var, state="readonly", width=15)
        self.class_combo.pack(side=tk.LEFT, padx=5)
        self.class_combo.bind("<<ComboboxSelected>>", self.on_brush_select)
        self.update_class_combo()
        
        ttk.Button(tools_frame, text="Save (Ctrl+S)", command=self.save_labels).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools_frame, text="Mark as BG (Shift+N)", command=self.mark_as_background).pack(side=tk.LEFT, padx=5)
        
        # Removed: Select Model, Confidence Controls (moved to Settings)

        
        ttk.Button(tools_frame, text="Auto-Label (O)", command=self.auto_label).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools_frame, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(tools_frame, text="Redo", command=self.redo).pack(side=tk.LEFT, padx=2)
        
        self.info_label = ttk.Label(tools_frame, text="No image loaded")
        self.info_label.pack(side=tk.RIGHT, padx=10)
        
        # Canvas Frame
        canvas_frame = ttk.Frame(middle_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 3. Right panel - Inspector
        right_panel = ttk.LabelFrame(self.main_paned, text="Boxes")
        self.main_paned.add(right_panel, minsize=150)
        
        self.inspector_listbox = tk.Listbox(right_panel, bg="#1e1e1e", fg="white", selectmode='extended')
        self.inspector_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.inspector_listbox.bind("<<ListboxSelect>>", self.on_inspector_select)
        
        ttk.Button(right_panel, text="Delete Box(es)", command=self.delete_selected_box).pack(pady=5)
        
        # Bind drawing events
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", self.on_canvas_leave)
        self.bind_all("<Control-s>", lambda e: self.save_labels())
        self.bind_all("<Control-z>", lambda e: self.undo())
        self.bind_all("<Control-y>", lambda e: self.redo())
        self.bind_all("<Delete>", self.handle_delete_key)
        self.bind_all("<Control-Shift-Delete>", lambda e: self.delete_current_image())
        self.bind_all("<Key-1>", lambda e: self.set_mode("edit"))
        self.bind_all("<Key-2>", lambda e: self.set_mode("draw"))
        self.bind_all("<Key-3>", lambda e: self.set_mode("magic"))
        self.bind_all("<Shift-N>", lambda e: self.mark_as_background())
        self.canvas.bind("<Key-r>", self.reset_view)
        self.canvas.focus_set()
        
        # Pan bindings
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)
        self.canvas.bind("<ButtonPress-3>", self.start_pan) 
        self.canvas.bind("<B3-Motion>", self.pan)
        
        # Zoom/Brush bindings (Canvas only)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)

        # Initial sash positioning for 10-80-10 distribution
        self.after(100, self._set_initial_sashes)
    
    def _set_initial_sashes(self):
        """Set initial sash positions for 10-80-10 layout."""
        width = self.winfo_width()
        if width > 100:
            sash1 = int(width * 0.1)
            sash2 = int(width * 0.9)
            try:
                self.main_paned.sash_place(0, sash1, 0)
                self.main_paned.sash_place(1, sash2, 0)
            except:
                pass

    
    def create_classes_tab(self):
        """Create the Classes tab with collapsible tree."""
        tab = ttk.Frame(self.notebook)
        
        controls = ttk.Frame(tab)
        controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls, text="Add Class", command=self.add_class).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text="Delete Class", command=self.delete_class).pack(side=tk.LEFT, padx=2)
        
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.class_tree = ttk.Treeview(tree_frame, selectmode='browse')
        self.class_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, command=self.class_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.class_tree.config(yscrollcommand=scrollbar.set)
        
        self.class_tree.bind("<<TreeviewSelect>>", self.on_class_tree_select)
        
        return tab
    
    def create_simple_tab(self, name):
        """Create a simple list tab."""
        tab = ttk.Frame(self.notebook)
        
        listbox = tk.Listbox(tab, bg="#1e1e1e", fg="white", selectmode='extended')
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        listbox.bind("<<ListboxSelect>>", lambda e: self.on_simple_list_select(e, name))
        
        safe_name = name.lower().replace(" ", "_")
        setattr(self, f"{safe_name}_listbox", listbox)
        return tab
    
    def update_class_combo(self):
        """Update the brush class selector."""
        classes = self.project_manager.get_classes()
        self.class_combo['values'] = classes
        if classes and not self.selected_class:
            self.class_combo.current(0)
            self.selected_class = classes[0]
    
    def on_brush_select(self, event):
        """Handle brush selection."""
        self.selected_class = self.class_var.get()
    
    def add_class(self):
        """Add a new class."""
        class_name = simpledialog.askstring("Add Class", "Enter class name:")
        if class_name:
            self.project_manager.add_class(class_name)
            self.update_class_combo()
            self.refresh_all_images()
    
    def delete_class(self):
        """Delete a class."""
        selection = self.class_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select a class folder to delete.")
            return
        
        item = selection[0]
        if self.class_tree.parent(item):
            messagebox.showwarning("Invalid", "Select a class folder, not an image.")
            return
        
        class_name = self.class_tree.item(item)["text"].split(" (")[0]
        
        if messagebox.askyesno("Delete Class", f"Delete '{class_name}' and all its images?"):
            self.project_manager.remove_class(class_name)
            self.update_class_combo()
            self.refresh_all_images()
    
    def refresh_all_images(self):
        """Refresh all image lists."""
        if not self.project_manager.current_project_path:
            return
        
        images_dir = os.path.join(self.project_manager.current_project_path, "data", "images")
        labels_dir = os.path.join(self.project_manager.current_project_path, "data", "labels")
        
        if not os.path.exists(images_dir):
            return
        
        # Categorize
        all_images = {"Classes": {}, "Unlabeled": [], "Verified BG": []}
        
        classes = self.project_manager.get_classes()
        for cls in classes:
            all_images["Classes"][cls] = []
        
        for img_file in os.listdir(images_dir):
            if not img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            
            img_path = os.path.join(images_dir, img_file)
            label_path = os.path.join(labels_dir, os.path.splitext(img_file)[0] + ".txt")
            
            # Check existence and content
            if os.path.exists(label_path):
                if os.path.getsize(label_path) > 0:
                    with open(label_path, "r") as f:
                        lines = f.readlines()
                        if lines:
                            try:
                                class_id = int(float(lines[0].split()[0]))
                                if class_id < len(classes):
                                    all_images["Classes"][classes[class_id]].append(img_path)
                            except:
                                # Could be empty or corrupted after all?
                                all_images["Verified BG"].append(img_path)
                        else:
                            all_images["Verified BG"].append(img_path)
                else:
                    # Exists but 0 bytes = Verified BG
                    all_images["Verified BG"].append(img_path)
            else:
                # No label file = Unlabeled (Inbox)
                all_images["Unlabeled"].append(img_path)
        
        # Update UI
        self.class_tree.delete(*self.class_tree.get_children())
        for cls, images in all_images["Classes"].items():
            parent = self.class_tree.insert("", "end", text=f"{cls} ({len(images)})")
            for img in images:
                self.class_tree.insert(parent, "end", text=os.path.basename(img), values=(img,))
        
        for category in ["Unlabeled", "Verified BG"]:
            listbox_name = category.lower().replace(" ", "_")
            listbox = getattr(self, f"{listbox_name}_listbox")
            listbox.delete(0, tk.END)
            for img in all_images[category]:
                listbox.insert(tk.END, os.path.basename(img))
            # Store paths for retrieval
            setattr(self, f"{listbox_name}_paths", all_images[category])
    
    def on_class_tree_select(self, event):
        """Handle class tree selection."""
        selection = self.class_tree.selection()
        if selection and self.class_tree.parent(selection[0]):
            img_path = self.class_tree.item(selection[0])["values"][0]
            self.selected_image_for_deletion = img_path  # Track for deletion
            self.load_image(img_path)
    
    def on_simple_list_select(self, event, category):
        """Handle simple list selection."""
        safe_name = category.lower().replace(" ", "_")
        listbox = getattr(self, f"{safe_name}_listbox")
        sel = listbox.curselection()
        if sel:
            paths = getattr(self, f"{safe_name}_paths", [])
            if sel[0] < len(paths):
                img_path = paths[sel[0]]
                self.selected_image_for_deletion = img_path  # Track for deletion
                self.load_image(img_path)
    
    def on_inspector_select(self, event):
        """Highlight selected box."""
        sel = self.inspector_listbox.curselection()
        if sel:
            self.selected_box_idx = sel[0]
            self._update_all_box_styles()
    
    def load_image(self, img_path):
        """Load image onto canvas."""
        self.current_image_path = img_path
        self.info_label.config(text=os.path.basename(img_path))
        
        try:
            self.pil_image = Image.open(img_path)
            self.img_width, self.img_height = self.pil_image.size

            

            # Reset state
            self.boxes = []
            self.selected_box_idx = None
            self.history = []
            self.redo_stack = []

            self.canvas.delete("all")
            
            self.load_existing_labels()
            self.reset_view()
            self.update_inspector()

            # self.load_existing_labels()
            # self.update_inspector()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
    

    def reset_view(self, event=None):
        """Fit image to canvas center."""
        if not self.pil_image: return
        
        self.img_width, self.img_height = self.pil_image.size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            scale_w = canvas_width / self.img_width
            scale_h = canvas_height / self.img_height
            self.scale = min(scale_w, scale_h)
            
            # Center it
            disp_w = self.img_width * self.scale
            disp_h = self.img_height * self.scale
            self.pan_x = (canvas_width - disp_w) / 2
            self.pan_y = (canvas_height - disp_h) / 2
        else:
            self.scale = 1.0
            self.pan_x = 0
            self.pan_y = 0
            
        self.redraw_view()

    def redraw_view(self):
        """Redraw the visible portion of the image at current scale."""
        if not self.pil_image: return
        
        # Canvas dimensions
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        if cw < 2: cw = 800
        if ch < 2: ch = 600

        img_w, img_h = self.pil_image.size
        
        # 1. Calculate Visible Rectangle in Image Coords
        # ix = (cx - pan_x) / scale
        vis_x1 = -self.pan_x / self.scale
        vis_y1 = -self.pan_y / self.scale
        vis_x2 = (cw - self.pan_x) / self.scale
        vis_y2 = (ch - self.pan_y) / self.scale
        
        # Intersect with Image Bounds
        crop_x1 = max(0, int(vis_x1))
        crop_y1 = max(0, int(vis_y1))
        crop_x2 = min(img_w, int(vis_x2) + 1)
        crop_y2 = min(img_h, int(vis_y2) + 1)
        
        # Store current boxes data to re-create
        current_boxes = self.boxes
        self.boxes = [] # Will be repopulated
        
        self.canvas.delete("all")

        # If completely off-screen, just redraw boxes (though likely none visible)
        if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
            pass
        else:
            # 2. Crop
            crop = self.pil_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            
            # 3. Resize
            target_w = int((crop_x2 - crop_x1) * self.scale)
            target_h = int((crop_y2 - crop_y1) * self.scale)
            
            # Use NEAREST for speed/sharpness when zoomed inside
            resample_method = Image.Resampling.NEAREST if self.scale >= 1.0 else Image.Resampling.BILINEAR
                
            display_img = crop.resize((max(1, target_w), max(1, target_h)), resample_method)
            self.photo_image = ImageTk.PhotoImage(display_img)
            
            # 4. Position on Canvas
            draw_x = self.pan_x + crop_x1 * self.scale
            draw_y = self.pan_y + crop_y1 * self.scale
            
            self.image_id = self.canvas.create_image(draw_x, draw_y, anchor=tk.NW, image=self.photo_image)
        
        # 5. Redraw boxes
        for box_data in current_boxes:
             x1, y1, x2, y2 = box_data['bbox']
             cls = box_data['class']
             self.add_box_to_canvas(x1, y1, x2, y2, cls)

    def zoom(self, delta, mouse_x, mouse_y):
        """Zoom in or out relative to mouse position."""
        if not self.pil_image: return
        
        # Zoom factor
        factor = 1.1 if delta > 0 else 0.9
        new_scale = self.scale * factor
        
        # Clamp
        new_scale = max(0.1, min(new_scale, 20.0))
        
        if new_scale == self.scale: return
        
        # Calculate offset adjustment to keep mouse_x/y over same image pixel
        # Mouse pos relative to image origin (pan)
        rel_x = mouse_x - self.pan_x
        rel_y = mouse_y - self.pan_y
        
        # Apply scaling factor to this relative vector
        # new_rel = rel * (new_scale / old_scale)
        scale_ratio = new_scale / self.scale
        
        new_rel_x = rel_x * scale_ratio
        new_rel_y = rel_y * scale_ratio
        
        # New pan position
        self.pan_x = mouse_x - new_rel_x
        self.pan_y = mouse_y - new_rel_y
        
        self.scale = new_scale
        self.redraw_view()
        
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self._pan_orig_x = self.pan_x
        self._pan_orig_y = self.pan_y

    def pan(self, event):
        # Calculate delta
        dx = event.x - self._pan_start_x
        dy = event.y - self._pan_start_y
        
        self.pan_x = self._pan_orig_x + dx
        self.pan_y = self._pan_orig_y + dy
        self.redraw_view()
    
    def load_existing_labels(self):
        """Load existing YOLO labels."""
        filename = os.path.basename(self.current_image_path)
        label_path = os.path.join(self.project_manager.current_project_path, "data", "labels",
                                    os.path.splitext(filename)[0] + ".txt")
        
        classes = self.project_manager.get_classes()
        if not os.path.exists(label_path):
            return
        
        with open(label_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls_idx = int(float(parts[0]))
                    cx, cy, w, h = map(float, parts[1:5])
                    
                    if cls_idx < len(classes):
                        x1 = (cx - w/2) * self.img_width
                        y1 = (cy - h/2) * self.img_height
                        x2 = (cx + w/2) * self.img_width
                        y2 = (cy + h/2) * self.img_height
                        
                        self.add_box_visual(x1, y1, x2, y2, classes[cls_idx])
    
    def on_canvas_motion(self, event):
        """Update crosshair position as mouse moves."""
        if not self.current_image_path:
            return
        
        # Remove old crosshairs
        if self.crosshair_x:
            self.canvas.delete(self.crosshair_x)
        if self.crosshair_y:
            self.canvas.delete(self.crosshair_y)
        
        # Draw new crosshairs
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Vertical line (X axis)
        self.crosshair_x = self.canvas.create_line(
            event.x, 0, event.x, canvas_height,
            fill="#00FF00", width=1, dash=(4, 4), tags="crosshair"
        )
        
        # Horizontal line (Y axis)
        self.crosshair_y = self.canvas.create_line(
            0, event.y, canvas_width, event.y,
            fill="#00FF00", width=1, dash=(4, 4), tags="crosshair"
        )
    
    def on_canvas_leave(self, event):
        """Remove crosshairs when mouse leaves canvas."""
        if self.crosshair_x:
            self.canvas.delete(self.crosshair_x)
            self.crosshair_x = None
        if self.crosshair_y:
            self.canvas.delete(self.crosshair_y)
            self.crosshair_y = None
    
    def on_canvas_press(self, event):
        if not self.current_image_path or not self.selected_class:
            return
            
        if getattr(self, 'labeling_mode', 'edit') == "edit":
            current = self.canvas.find_withtag("current")
            clicked_box_idx = None
            for item in current:
                if "box" in self.canvas.gettags(item):
                    for i, box in enumerate(self.boxes):
                        if box['id'] == item or box['text_id'] == item:
                            clicked_box_idx = i
                            break
                    if clicked_box_idx is not None:
                        break
            
            if clicked_box_idx is None:
                # Check for internal click
                for i, box in enumerate(self.boxes):
                    x1, y1, x2, y2 = box['bbox']
                    sx1, sy1 = x1 * self.scale + self.pan_x, y1 * self.scale + self.pan_y
                    sx2, sy2 = x2 * self.scale + self.pan_x, y2 * self.scale + self.pan_y
                    xmin, xmax = min(sx1, sx2), max(sx1, sx2)
                    ymin, ymax = min(sy1, sy2), max(sy1, sy2)
                    if xmin <= event.x <= xmax and ymin <= event.y <= ymax:
                        clicked_box_idx = i
                        break

            if clicked_box_idx is not None:
                self.selected_box_idx = clicked_box_idx
                self.inspector_listbox.selection_clear(0, tk.END)
                self.inspector_listbox.selection_set(clicked_box_idx)
                self.inspector_listbox.event_generate("<<ListboxSelect>>")
                
                box = self.boxes[clicked_box_idx]
                x1, y1, x2, y2 = box['bbox']
                # ... rest of resize corner logic ...
                sx1, sy1 = x1 * self.scale + self.pan_x, y1 * self.scale + self.pan_y
                sx2, sy2 = x2 * self.scale + self.pan_x, y2 * self.scale + self.pan_y
                
                threshold = 15
                self.resize_corner = None
                self.moving_box_start = (event.x, event.y)
                self.moving_box_idx = clicked_box_idx
                self.original_bbox = [x1, y1, x2, y2]
                
                if abs(event.x - sx1) < threshold and abs(event.y - sy1) < threshold: self.resize_corner = "NW"
                elif abs(event.x - sx2) < threshold and abs(event.y - sy1) < threshold: self.resize_corner = "NE"
                elif abs(event.x - sx1) < threshold and abs(event.y - sy2) < threshold: self.resize_corner = "SW"
                elif abs(event.x - sx2) < threshold and abs(event.y - sy2) < threshold: self.resize_corner = "SE"
                elif abs(event.x - sx1) < threshold: self.resize_corner = "W"
                elif abs(event.x - sx2) < threshold: self.resize_corner = "E"
                elif abs(event.y - sy1) < threshold: self.resize_corner = "N"
                elif abs(event.y - sy2) < threshold: self.resize_corner = "S"
                else: self.resize_corner = "MOVE"
            else:
                self.moving_box_idx = None
                self.selected_box_idx = None
                self._update_all_box_styles()
            return

        elif getattr(self, 'labeling_mode', 'edit') == "draw":
            self.current_box_start = (event.x, event.y)
            self.drawing_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)
            
        elif getattr(self, 'labeling_mode', 'edit') == "magic":
            self.current_box_start = (event.x, event.y)
            self.drawing_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#33ccff", width=2, dash=(4, 4))
    
    def on_canvas_drag(self, event):
        if getattr(self, 'labeling_mode', 'edit') == "edit":
            if getattr(self, 'moving_box_idx', None) is not None:
                dx = event.x - self.moving_box_start[0]
                dy = event.y - self.moving_box_start[1]
                self.moving_box_start = (event.x, event.y)
                
                box = self.boxes[self.moving_box_idx]
                idx = dx / self.scale
                idy = dy / self.scale
                
                x1, y1, x2, y2 = box['bbox']
                if self.resize_corner == "NW": x1 += idx; y1 += idy
                elif self.resize_corner == "NE": x2 += idx; y1 += idy
                elif self.resize_corner == "SW": x1 += idx; y2 += idy
                elif self.resize_corner == "SE": x2 += idx; y2 += idy
                elif self.resize_corner == "W": x1 += idx
                elif self.resize_corner == "E": x2 += idx
                elif self.resize_corner == "N": y1 += idy
                elif self.resize_corner == "S": y2 += idy
                elif self.resize_corner == "MOVE":
                    x1 += idx; x2 += idx; y1 += idy; y2 += idy
                    
                box['bbox'] = [x1, y1, x2, y2]
                
                sx1, sy1 = x1 * self.scale + self.pan_x, y1 * self.scale + self.pan_y
                sx2, sy2 = x2 * self.scale + self.pan_x, y2 * self.scale + self.pan_y
                self.canvas.coords(box['id'], sx1, sy1, sx2, sy2)
                self.canvas.coords(box['text_id'], min(sx1,sx2), min(sy1,sy2)-10)
            return

        if self.current_box_start and getattr(self, 'drawing_rect_id', None):
            x, y = self.current_box_start
            self.canvas.coords(self.drawing_rect_id, x, y, event.x, event.y)
    
    def on_canvas_release(self, event):
        if getattr(self, 'labeling_mode', 'edit') == "edit":
            if getattr(self, 'moving_box_idx', None) is not None:
                box = self.boxes[self.moving_box_idx]
                x1, y1, x2, y2 = box['bbox']
                x1, x2 = sorted([x1, x2])
                y1, y2 = sorted([y1, y2])
                box['bbox'] = [x1, y1, x2, y2]
                sx1, sy1 = x1 * self.scale + self.pan_x, y1 * self.scale + self.pan_y
                sx2, sy2 = x2 * self.scale + self.pan_x, y2 * self.scale + self.pan_y
                self.canvas.coords(box['id'], sx1, sy1, sx2, sy2)
                self.canvas.coords(box['text_id'], sx1, sy1-10)
                
                self.history.append(('edit', box, self.original_bbox))
                self.moving_box_idx = None
                self.redo_stack.clear()
            return
            
        if self.current_box_start and getattr(self, 'drawing_rect_id', None):
            x1, y1 = self.current_box_start
            x2, y2 = event.x, event.y
            
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])
            
            if getattr(self, 'labeling_mode', 'edit') == "draw":
                if (x2 - x1) > 5 and (y2 - y1) > 5:
                    img_x1, img_y1 = (x1 - self.pan_x) / self.scale, (y1 - self.pan_y) / self.scale
                    img_x2, img_y2 = (x2 - self.pan_x) / self.scale, (y2 - self.pan_y) / self.scale
                    self.add_box_visual(img_x1, img_y1, img_x2, img_y2, self.selected_class, record_history=True)
                self.canvas.delete(self.drawing_rect_id)
                self.current_box_start = None
                self.drawing_rect_id = None
            
            elif getattr(self, 'labeling_mode', 'edit') == "magic":
                img_x1, img_y1 = (x1 - self.pan_x) / self.scale, (y1 - self.pan_y) / self.scale
                img_x2, img_y2 = (x2 - self.pan_x) / self.scale, (y2 - self.pan_y) / self.scale
                
                self.canvas.delete(self.drawing_rect_id)
                self.current_box_start = None
                self.drawing_rect_id = None
                
                if not getattr(self, 'sam_wrapper', None):
                    self._init_sam_if_needed()
                    if not getattr(self, 'sam_wrapper', None): return
                
                try:
                    self.canvas.config(cursor="watch")
                    self.update_idletasks()
                    if (x2 - x1) > 5 and (y2 - y1) > 5:
                        bbox = self.sam_wrapper.predict_box(self.current_image_path, [img_x1, img_y1, img_x2, img_y2])
                    else:
                        bbox = self.sam_wrapper.predict_point(self.current_image_path, (img_x1, img_y1))
                    
                    self.canvas.config(cursor="target")
                    if bbox:
                        bx1, by1, bx2, by2 = bbox
                        self.add_box_visual(bx1, by1, bx2, by2, self.selected_class, record_history=True)
                    else:
                        self.flash_feedback()
                except Exception as e:
                    print(f"Magic Wand Error: {e}")
                    self.canvas.config(cursor="target")
                    self.flash_feedback()
    
    def add_box_visual(self, x1, y1, x2, y2, cls_name, record_history=False):
        """Add a box to the canvas."""
        sx1, sy1 = x1 * self.scale + self.pan_x, y1 * self.scale + self.pan_y
        sx2, sy2 = x2 * self.scale + self.pan_x, y2 * self.scale + self.pan_y
        
        color = self.get_class_color(cls_name)
        
        rect_id = self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline=color, width=2, tags="box")
        text_id = self.canvas.create_text(sx1, sy1-10, text=cls_name, fill=color, anchor=tk.SW, tags="box")
        
        self._bind_box(rect_id, text_id, color)
        
        box = {"id": rect_id, "text_id": text_id, "class": cls_name, "bbox": [x1, y1, x2, y2]}
        self.boxes.append(box)
        self.update_inspector()
        
        if record_history:
            self.history.append(("add", box))
            self.redo_stack.clear()

    def save_history(self):
        """Save current state to history for undo."""
        pass
    
    def _bind_box(self, rect_id, text_id, color):
        self.canvas.tag_bind(rect_id, "<Enter>", lambda e, bid=rect_id, c=color: self.on_box_enter(bid, c))
        self.canvas.tag_bind(rect_id, "<Leave>", lambda e, bid=rect_id, c=color: self.on_box_leave(bid, c))
        self.canvas.tag_bind(text_id, "<Enter>", lambda e, bid=rect_id, c=color: self.on_box_enter(bid, c))
        self.canvas.tag_bind(text_id, "<Leave>", lambda e, bid=rect_id, c=color: self.on_box_leave(bid, c))

    def on_box_enter(self, bid, color):
        try:
            if self.canvas.type(bid) == "rectangle":
                self.canvas.itemconfig(bid, fill=color, stipple='gray25', width=4)
        except tk.TclError:
            pass

    def on_box_leave(self, bid, color):
        try:
            if self.canvas.type(bid) == "rectangle":
                is_selected = False
                for i, box in enumerate(self.boxes):
                    if box['id'] == bid and i == getattr(self, 'selected_box_idx', None):
                        is_selected = True
                        break
                
                if is_selected:
                    self.canvas.itemconfig(bid, fill='', stipple='', width=4)
                else:
                    self.canvas.itemconfig(bid, fill='', stipple='', width=2)
        except tk.TclError:
            pass

    def _update_all_box_styles(self):
        """Update widths and fills for all boxes based on selection state."""
        for i, box in enumerate(self.boxes):
            width = 4 if i == getattr(self, 'selected_box_idx', None) else 2
            try:
                self.canvas.itemconfig(box['id'], width=width)
            except tk.TclError:
                pass

    
    def update_inspector(self):
        """Update the inspector listbox."""
        self.inspector_listbox.delete(0, tk.END)
        for i, box in enumerate(self.boxes):
            self.inspector_listbox.insert(tk.END, f"{i}: {box['class']}")
    
    def delete_selected_box(self):
        """Delete the selected box(es)."""
        selections = self.inspector_listbox.curselection()
        if not selections:
            return
        
        # Sort in reverse to delete from end to start (preserves indices)
        for idx in sorted(selections, reverse=True):
            if idx < len(self.boxes):
                box = self.boxes.pop(idx)
                self.canvas.delete(box['id'])
                self.canvas.delete(box['text_id'])
                self.history.append(("delete", box, idx))
        
        self.redo_stack.clear()
        self.update_inspector()
    
    def unload_sam(self):
        """Unload SAM model to free memory (e.g., before training)."""
        if self.sam_wrapper is not None:
            print("[Memory] Unloading SAM model...")
            del self.sam_wrapper
            self.sam_wrapper = None
            import gc
            gc.collect()
            print("[Memory] SAM model unloaded")
    
    def reload_sam(self):
        """Reload SAM model (e.g., after training completes)."""
        if self.sam_wrapper is None:
            print("[Memory] Reloading SAM model...")
            # Get model path from project config, fallback to default
            model_path = self.project_manager.project_config.get("auto_label_model", "sam2.1_l.pt")
            from app.core.sam_wrapper import SAMWrapper
            try:
                self.sam_wrapper = SAMWrapper(model_path=model_path)
                print("[Memory] SAM model reloaded")
            except Exception as e:
                print(f"[Memory] Failed to reload SAM: {e}")
    
    def undo(self):
        """Undo last action."""
        if not self.history:
            return
        action = self.history.pop()
        
        if action[0] == 'add':
            box = action[1]
            self.boxes.remove(box)
            self.canvas.delete(box['id'])
            self.canvas.delete(box['text_id'])
            self.redo_stack.append(action)
        elif action[0] == 'delete':
            box, idx = action[1], action[2]
            self.boxes.insert(idx, box)
            sx1, sy1 = box['bbox'][0] * self.scale + self.pan_x, box['bbox'][1] * self.scale + self.pan_y
            sx2, sy2 = box['bbox'][2] * self.scale + self.pan_x, box['bbox'][3] * self.scale + self.pan_y
            color = self.get_class_color(box['class'])
            box['id'] = self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline=color, width=2, tags="box")
            box['text_id'] = self.canvas.create_text(sx1, sy1-10, text=box['class'], fill=color, anchor=tk.SW, tags="box")
            self._bind_box(box['id'], box['text_id'], color)
            self.redo_stack.append(action)
        elif action[0] == 'edit':
            box, old_bbox = action[1], action[2]
            new_bbox = box['bbox'].copy()
            box['bbox'] = old_bbox
            sx1, sy1 = old_bbox[0] * self.scale + self.pan_x, old_bbox[1] * self.scale + self.pan_y
            sx2, sy2 = old_bbox[2] * self.scale + self.pan_x, old_bbox[3] * self.scale + self.pan_y
            self.canvas.coords(box['id'], sx1, sy1, sx2, sy2)
            self.canvas.coords(box['text_id'], min(sx1,sx2), min(sy1,sy2)-10)
            self.redo_stack.append(('edit', box, new_bbox))
        
        self.update_inspector()
    
    def redo(self):
        """Redo last undone action."""
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        
        if action[0] == 'add':
            self.add_box_visual(*action[1]['bbox'], action[1]['class'], record_history=False)
            self.history.append(action)
        elif action[0] == 'delete':
            box = action[1]
            if box in self.boxes:
                self.boxes.remove(box)
                self.canvas.delete(box['id'])
                self.canvas.delete(box['text_id'])
                self.history.append(action)
        elif action[0] == 'edit':
            box, new_bbox = action[1], action[2]
            old_bbox = box['bbox'].copy()
            box['bbox'] = new_bbox
            sx1, sy1 = new_bbox[0] * self.scale + self.pan_x, new_bbox[1] * self.scale + self.pan_y
            sx2, sy2 = new_bbox[2] * self.scale + self.pan_x, new_bbox[3] * self.scale + self.pan_y
            self.canvas.coords(box['id'], sx1, sy1, sx2, sy2)
            self.canvas.coords(box['text_id'], min(sx1,sx2), min(sy1,sy2)-10)
            self.history.append(('edit', box, old_bbox))
        
        self.update_inspector()
    
    def save_labels(self):
        """Save labels to YOLO format."""
        if not self.current_image_path:
            return
        
        filename = os.path.basename(self.current_image_path)
        label_path = os.path.join(self.project_manager.current_project_path, "data", "labels",
                                    os.path.splitext(filename)[0] + ".txt")
        
        classes = self.project_manager.get_classes()
        
        # Determine if it's a Verified BG or has content
        if not self.boxes:
            # Explicitly save empty for background
            with open(label_path, "w") as f:
                pass
        else:
            with open(label_path, "w") as f:
                for box in self.boxes:
                    cls_name = box['class']
                    if cls_name in classes:
                        cls_idx = classes.index(cls_name)
                        x1, y1, x2, y2 = box['bbox']
                        
                        # Normalize
                        cx = ((x1 + x2) / 2) / self.img_width
                        cy = ((y1 + y2) / 2) / self.img_height
                        w = abs(x2 - x1) / self.img_width
                        h = abs(y2 - y1) / self.img_height
                        
                        f.write(f"{cls_idx} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
        
        # Get next path BEFORE refreshing UI to know where we were
        next_path = self.get_next_image_path()
        
        self.flash_feedback()
        self.refresh_all_images()
        
        # Navigate to next image if available
        if next_path:
            self.load_image(next_path)
            self.select_path_in_ui(next_path)

    def mark_as_background(self):
        """Explicitly confirm current image as a Verified Background."""
        if not self.current_image_path:
            return
        
        # Clear any existing boxes
        self.boxes = []
        self.canvas.delete("box")
        
        # Trigger save as empty
        self.save_labels()
    
    def import_images(self):
        """Import images."""
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All", "*.*")]
        )
        
        if files:
            images_dir = os.path.join(self.project_manager.current_project_path, "data", "images")
            for file in files:
                shutil.copy2(file, images_dir)
            messagebox.showinfo("Success", f"Imported {len(files)} images.")
            self.refresh_all_images()
    
    def handle_delete_key(self, event):
        """Handle delete key - delete box or image depending on context."""
        # Priority: Inspector > Tab selections > Current image
        if self.inspector_listbox.curselection():
            self.delete_selected_box()
        elif self.class_tree.selection():
            # Check if it's an image in class tree
            sel = self.class_tree.selection()[0]
            if self.class_tree.parent(sel):  # It's an image
                self.delete_selected_image_from_tab()
        elif self.unlabeled_listbox.curselection():
            self.delete_selected_image_from_tab()
        elif self.verified_bg_listbox.curselection():
            self.delete_selected_image_from_tab()
    
    def delete_selected_image_from_tab(self):
        """Delete image(s) selected in any tab."""
        # Collect all selected images
        images_to_delete = []
        
        # Check class tree
        if self.class_tree.selection():
            for sel in self.class_tree.selection():
                if self.class_tree.parent(sel):  # It's an image
                    img_path = self.class_tree.item(sel)["values"][0]
                    images_to_delete.append(img_path)
        
        # Check unlabeled listbox
        unlabeled_selections = self.unlabeled_listbox.curselection()
        if unlabeled_selections:
            for idx in unlabeled_selections:
                if idx < len(self.unlabeled_paths):
                    images_to_delete.append(self.unlabeled_paths[idx])
        
        # Check verified bg listbox
        vbg_selections = self.verified_bg_listbox.curselection()
        if vbg_selections:
            for idx in vbg_selections:
                if idx < len(self.verified_bg_paths):
                    images_to_delete.append(self.verified_bg_paths[idx])
        
        if not images_to_delete:
            return
        
        # Confirm deletion
        count = len(images_to_delete)
        if count == 1:
            filename = os.path.basename(images_to_delete[0])
            if not messagebox.askyesno("Delete", f"Delete {filename}?"):
                return
        else:
            if not messagebox.askyesno("Delete Multiple", f"Delete {count} image(s)?"):
                return
        
        # Delete all selected images
        for img_path in images_to_delete:
            try:
                filename = os.path.basename(img_path)
                # Delete image
                if os.path.exists(img_path):
                    os.remove(img_path)
                
                # Delete label
                label_path = os.path.join(
                    self.project_manager.current_project_path, "data", "labels",
                    os.path.splitext(filename)[0] + ".txt"
                )
                if os.path.exists(label_path):
                    os.remove(label_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {filename}: {e}")
        
        self.selected_image_for_deletion = None
        self.current_image_path = None
        self.refresh_all_images()
        
        if count == 1:
            messagebox.showinfo("Deleted", f"Deleted 1 image")
        else:
            messagebox.showinfo("Deleted", f"Deleted {count} images")
    
    def delete_current_image(self):
        """Delete the currently displayed image."""
        if not self.current_image_path:
            return
        
        filename = os.path.basename(self.current_image_path)
        if messagebox.askyesno("Delete Image", f"Delete {filename}?"):
            try:
                os.remove(self.current_image_path)
                
                # Delete label
                label_path = os.path.join(
                    self.project_manager.current_project_path, "data", "labels",
                    os.path.splitext(filename)[0] + ".txt"
                )
                if os.path.exists(label_path):
                    os.remove(label_path)
                
                self.refresh_all_images()
                messagebox.showinfo("Deleted", f"Deleted {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for Zoom (Ctrl) or Brush Change."""
        
        # Determine direction
        delta = 0
        # print(f"DEBUG: MouseWheel num={event.num} delta={getattr(event, 'delta', 'N/A')} state={event.state}")
        if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            delta = -1 # Down / Out
        elif event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            delta = 1 # Up / In
            
        if delta == 0: return

        # Check for Control key (Zoom)
        if (event.state & 0x0004) or (event.state & 4):
             # event.x/y are relative to canvas because we bound to self.canvas
             self.zoom(delta, event.x, event.y)
             return

        # Otherwise Change Brush
        classes = self.project_manager.get_classes()
        if not classes:
            return
        
        current_idx = 0
        if self.selected_class in classes:
            current_idx = classes.index(self.selected_class)
        
        new_idx = (current_idx + delta) % len(classes)
        self.selected_class = classes[new_idx]
        self.class_var.set(self.selected_class)
        
        # Check if widget still exists before updating
        try:
            self.class_combo.current(new_idx)
        except tk.TclError:
            pass  # Widget was destroyed, ignore

    # Removed select_auto_label_model, using project_settings now

    def set_mode(self, mode):
        """Switch labeling mode: 'edit', 'draw', or 'magic'."""
        self.labeling_mode = mode
        
        try:
            self.btn_edit.config(bg="#444" if mode == "edit" else "#2b2b2b")
            self.btn_draw.config(bg="#444" if mode == "draw" else "#2b2b2b")
            self.btn_magic.config(bg="#444" if mode == "magic" else "#2b2b2b")
        except:
            pass
            
        if mode == "magic":
            self.canvas.config(cursor="target")
            self._init_sam_if_needed()
        elif mode == "draw":
            self.canvas.config(cursor="crosshair")
        else:
            self.canvas.config(cursor="arrow")

    def _init_sam_if_needed(self):
        if self.labeling_mode == "magic" and not getattr(self, 'sam_wrapper', None):
             try:
                 use_cuda = self.project_manager.get_setting("use_cuda_labeling", "True").lower() == 'true'
                 device = 'cuda' if use_cuda else 'cpu'
                 self.sam_wrapper = SAMWrapper(device=device)
             except Exception as e:
                 messagebox.showerror("Error", f"Failed to init SAM2: {e}")
                 self.set_mode("edit")

    def auto_label(self):
        """Run YOLO inference to auto-label the current image."""
        if not self.current_image_path:
            return  # Silent return or maybe flash? No, silent is better if no image.

        # 1. Ensure Model from Settings
        model_path = self.project_manager.get_setting("auto_label_model")
        if not model_path or not os.path.exists(model_path):
             messagebox.showwarning("No Model", "Please select an Auto-Labeling model in JIET > Settings.")
             return

        try:
            # 2. Run Inference
            from app.core.yolo_wrapper import YOLOWrapper
            # We can instantiate wrapper lightly or reuse if available in project manager
            wrapper = YOLOWrapper(self.project_manager.current_project_path)
            
            # Run with user specified confidence
            conf = float(self.project_manager.get_setting("auto_label_confidence", 0.5))
            
            # Check settings for CUDA
            use_cuda = self.project_manager.get_setting("use_cuda_labeling", "True").lower() == 'true'
            device = 'cuda' if use_cuda else 'cpu'
            
            results = wrapper.run_inference(model_path, self.current_image_path, conf=conf, device=device)
            
            # 3. Process Results
            added_count = 0
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    class_name = r.names[cls_id]
                    
                    if class_name not in self.project_manager.get_classes():
                         # Automatically add class if possible or skip?
                         # User asked for simplified flow. Let's auto-add if missing or skip silently?
                         # The previous "popup" was annoying.
                         # Let's add it silently if we can, or just log.
                         # Safer: Add it silently.
                         self.project_manager.add_class(class_name)
                         self.update_class_combo()
                            
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    self.add_box_to_canvas(x1, y1, x2, y2, class_name)
                    added_count += 1
            
            if added_count > 0:
                pass  # Boxes already added with record_history=True
                # No popup
            else:
                self.flash_feedback()
                
        except Exception as e:
            # Only show error if it's a real crash, but maybe just log to console to not annoy user
            print(f"Auto-label error: {e}")
            self.flash_feedback() # Flash to indicate failure too?

    def flash_feedback(self):
        """Flash the canvas green with 50% transparency for 0.1s."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w <= 1 or h <= 1: return
            
        try:
            # Green flash (0, 255, 0)
            flash = Image.new("RGBA", (w, h), (0, 255, 0, 128))
            self._flash_photo = ImageTk.PhotoImage(flash) # Keep reference
            
            flash_id = self.canvas.create_image(0, 0, image=self._flash_photo, anchor="nw")
            
            self.after(100, lambda: self.canvas.delete(flash_id))
        except Exception as e:
            print(f"Flash error: {e}")

    def get_class_color(self, class_name):
        """Generate a deterministic color for a class."""
        # Simple hash based color
        h = hash(class_name)
        # Ensure positive
        if h < 0: h = -h
        # Hue based on hash
        r = (h % 255)
        g = ((h >> 8) % 255)
        b = ((h >> 16) % 255)
        # Ensure it's not too dark
        if r + g + b < 300:
             r = min(255, r + 100)
             g = min(255, g + 100)
             b = min(255, b + 100)
        return f"#{r:02x}{g:02x}{b:02x}"

    def add_box_to_canvas(self, x1, y1, x2, y2, class_name):
        """Helper to add a box from coordinates. Redirects to add_box_visual with history."""
        self.add_box_visual(x1, y1, x2, y2, class_name, record_history=True)

    def get_next_image_path(self):
        """Find the path of the next image in the current UI context."""
        tab_idx = self.notebook.index(self.notebook.select())
        
        if tab_idx == 0:  # Classes tab (Treeview)
            items = []
            def collect_images(parent):
                for item in self.class_tree.get_children(parent):
                    if self.class_tree.parent(item): # It's an image
                        items.append(item)
                    collect_images(item)
            
            for root_item in self.class_tree.get_children(''):
                collect_images(root_item)
                
            selection = self.class_tree.selection()
            if selection and selection[0] in items:
                idx = items.index(selection[0])
                if idx + 1 < len(items):
                    return self.class_tree.item(items[idx + 1])["values"][0]
        
        elif tab_idx == 1:  # Unlabeled tab
            sel = self.unlabeled_listbox.curselection()
            if sel:
                next_idx = sel[0] + 1
                if next_idx < len(self.unlabeled_paths):
                    return self.unlabeled_paths[next_idx]
        
        elif tab_idx == 2:  # Verified BG tab
            sel = self.verified_bg_listbox.curselection()
            if sel:
                next_idx = sel[0] + 1
                if next_idx < len(self.verified_bg_paths):
                    return self.verified_bg_paths[next_idx]
        
        return None

    def select_path_in_ui(self, target_path):
        """Try to find and select a specific image path in the UI."""
        tab_idx = self.notebook.index(self.notebook.select())
        
        if tab_idx == 0:  # Classes tab
            def find_and_select(parent):
                for item in self.class_tree.get_children(parent):
                    if self.class_tree.parent(item):
                        path = self.class_tree.item(item)["values"][0]
                        if path == target_path:
                            self.class_tree.selection_set(item)
                            self.class_tree.see(item)
                            return True
                    if find_and_select(item):
                        return True
                return False
            
            for root_item in self.class_tree.get_children(''):
                if find_and_select(root_item):
                    break
                    
        elif tab_idx == 1:  # Unlabeled tab
            for i, path in enumerate(self.unlabeled_paths):
                if path == target_path:
                    self.unlabeled_listbox.selection_clear(0, tk.END)
                    self.unlabeled_listbox.selection_set(i)
                    self.unlabeled_listbox.see(i)
                    break
        
        elif tab_idx == 2:  # Verified BG tab
            for i, path in enumerate(self.verified_bg_paths):
                if path == target_path:
                    self.verified_bg_listbox.selection_clear(0, tk.END)
                    self.verified_bg_listbox.selection_set(i)
                    self.verified_bg_listbox.see(i)
                    break
    


    # Legacy Magic Wand methods were removed and integrated natively into on_canvas_release.
