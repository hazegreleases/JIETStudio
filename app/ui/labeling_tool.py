import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from app.ui.components import RoundedButton
from PIL import Image, ImageTk
import os
import shutil
from app.core.theme_manager import ThemeManager

class LabelingTool(tk.Frame):
    def __init__(self, parent, project_manager):
        super().__init__(parent)
        self.project_manager = project_manager
        self.images = []
        self.current_image_index = -1
        self.current_image_path = None
        self.photo_image = None # Keep reference
        self.scale = 1.0
        
        self.boxes = [] # List of dicts: {'id': canvas_id, 'class': class_name, 'bbox': [x1, y1, x2, y2]}
        self.current_box_start = None
        self.drawing_rect_id = None
        
        # Crosshair guides
        self.crosshair_x = None
        self.crosshair_y = None
        
        self.history = [] # Stack for undo
        self.redo_stack = []

        self.selected_class = None
        
        self._create_ui()
        self._bind_events()
        self.refresh_image_list()
        self.refresh_class_list()

    def _create_ui(self):
        # Top Toolbar
        toolbar = tk.Frame(self, bg="#ddd", height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        RoundedButton(toolbar, text="Import Images", command=self.import_images, width=120, height=30).pack(side=tk.LEFT, padx=5, pady=5)
        RoundedButton(toolbar, text="Save (Ctrl+S)", command=self.save_labels, width=120, height=30).pack(side=tk.LEFT, padx=5, pady=5)
        RoundedButton(toolbar, text="Prev", command=self.prev_image, width=80, height=30).pack(side=tk.LEFT, padx=5, pady=5)
        RoundedButton(toolbar, text="Next", command=self.next_image, width=80, height=30).pack(side=tk.LEFT, padx=5, pady=5)
        RoundedButton(toolbar, text="Undo (Ctrl+Z)", command=self.undo, width=100, height=30).pack(side=tk.LEFT, padx=5, pady=5)
        RoundedButton(toolbar, text="Redo (Ctrl+Y)", command=self.redo, width=100, height=30).pack(side=tk.LEFT, padx=5, pady=5)

        # Main Content
        content = tk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True)

        # Left Sidebar (Image List)
        left_panel = tk.Frame(content, width=200, bg="#f0f0f0")
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(left_panel, text="Images", bg="#ccc").pack(fill=tk.X)
        self.image_listbox = tk.Listbox(left_panel, selectmode='extended')
        self.image_listbox.pack(fill=tk.BOTH, expand=True)
        self.image_listbox.bind("<<ListboxSelect>>", self.on_image_select)

        # Right Sidebar (Classes & Inspector)
        right_panel = tk.Frame(content, width=250, bg="#f0f0f0")
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Class List
        tk.Label(right_panel, text="Classes", bg="#ccc").pack(fill=tk.X)
        self.class_listbox = tk.Listbox(right_panel, height=10)
        self.class_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.class_listbox.bind("<<ListboxSelect>>", self.on_class_select)
        
        class_btn_frame = tk.Frame(right_panel, bg="#f0f0f0")
        class_btn_frame.pack(fill=tk.X, padx=5)
        RoundedButton(class_btn_frame, text="+", command=self.add_class, width=30, height=30).pack(side=tk.LEFT, padx=2)
        RoundedButton(class_btn_frame, text="-", command=self.remove_class, width=30, height=30).pack(side=tk.LEFT, padx=2)

        # Inspector
        tk.Label(right_panel, text="Inspector (Boxes)", bg="#ccc").pack(fill=tk.X, pady=(10, 0))
        self.inspector_listbox = tk.Listbox(right_panel, selectmode='extended')
        self.inspector_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.inspector_listbox.bind("<<ListboxSelect>>", self.on_inspector_select)
        RoundedButton(right_panel, text="Delete Box(es) (Del)", command=self.delete_selected_box, width=150, height=30).pack(pady=5)

        # Center Canvas
        self.canvas_frame = tk.Frame(content, bg="#888")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#888", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", self.on_canvas_leave)
        
        self.bind_all("<Control-s>", lambda e: self.save_labels())
        self.bind_all("<Control-z>", lambda e: self.undo())
        self.bind_all("<Control-y>", lambda e: self.redo())
        self.bind_all("<Delete>", self.handle_delete_key)
        self.bind_all("<Control-Shift-D>", lambda e: self.delete_current_image())
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel) # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)   # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)   # Linux scroll down

    def import_images(self):
        file_paths = filedialog.askopenfilenames(title="Select Images", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
        if not file_paths: return

        dest_dir = os.path.join(self.project_manager.current_project_path, "data", "images")
        for src in file_paths:
            shutil.copy(src, dest_dir)
        
        self.refresh_image_list()

    def refresh_image_list(self):
        self.image_listbox.delete(0, tk.END)
        img_dir = os.path.join(self.project_manager.current_project_path, "data", "images")
        self.images = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        non_labeled_color = ThemeManager().get("inspector_non_labeled_color")
        
        for i, img in enumerate(self.images):
            self.image_listbox.insert(tk.END, img)
            
            # Check if label exists
            label_name = os.path.splitext(img)[0] + ".txt"
            label_path = os.path.join(self.project_manager.current_project_path, "data", "labels", label_name)
            
            if not os.path.exists(label_path) or os.path.getsize(label_path) == 0:
                self.image_listbox.itemconfig(i, {'bg': non_labeled_color})

    def refresh_class_list(self):
        self.class_listbox.delete(0, tk.END)
        classes = self.project_manager.get_classes()
        for c in classes:
            self.class_listbox.insert(tk.END, c)
        
        if classes:
            self.class_listbox.select_set(0)
            self.selected_class = classes[0]

    def add_class(self):
        name = simpledialog.askstring("New Class", "Enter Class Name:")
        if name:
            self.project_manager.add_class(name)
            self.refresh_class_list()

    def remove_class(self):
        sel = self.class_listbox.curselection()
        if sel:
            name = self.class_listbox.get(sel[0])
            self.project_manager.remove_class(name)
            self.refresh_class_list()

    def on_class_select(self, event):
        sel = self.class_listbox.curselection()
        if sel:
            self.selected_class = self.class_listbox.get(sel[0])

    def on_image_select(self, event):
        sel = self.image_listbox.curselection()
        if sel:
            index = sel[0]
            self.load_image(index)

    def load_image(self, index):
        if 0 <= index < len(self.images):
            # Auto save previous if needed? Maybe explicit save is better for now as per user request "Ctrl+S to save and next"
            self.current_image_index = index
            filename = self.images[index]
            self.current_image_path = os.path.join(self.project_manager.current_project_path, "data", "images", filename)
            
            pil_img = Image.open(self.current_image_path)
            self.img_width, self.img_height = pil_img.size
            
            # Resize for display if too large (simple fit)
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # Simple scaling logic (can be improved)
            if canvas_width > 1 and canvas_height > 1:
                scale_w = canvas_width / self.img_width
                scale_h = canvas_height / self.img_height
                self.scale = min(scale_w, scale_h, 1.0)
            else:
                self.scale = 1.0

            display_w = int(self.img_width * self.scale)
            display_h = int(self.img_height * self.scale)
            
            pil_img_resized = pil_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
            self.photo_image = ImageTk.PhotoImage(pil_img_resized)
            
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
            
            self.boxes = []
            self.history = []
            self.redo_stack = []
            self.load_existing_labels(filename)
            self.update_inspector()

    def load_existing_labels(self, filename):
        label_name = os.path.splitext(filename)[0] + ".txt"
        label_path = os.path.join(self.project_manager.current_project_path, "data", "labels", label_name)
        
        classes = self.project_manager.get_classes()
        
        if os.path.exists(label_path):
            with open(label_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_idx = int(float(parts[0]))
                        cx, cy, w, h = map(float, parts[1:5])
                        
                        if 0 <= cls_idx < len(classes):
                            cls_name = classes[cls_idx]
                            
                            # Convert YOLO to pixel
                            x1 = (cx - w/2) * self.img_width
                            y1 = (cy - h/2) * self.img_height
                            x2 = (cx + w/2) * self.img_width
                            y2 = (cy + h/2) * self.img_height
                            
                            self.add_box_visual(x1, y1, x2, y2, cls_name)

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
        if not self.current_image_path: return
        
        current = self.canvas.find_withtag("current")
        is_box = False
        for item in current:
            if "box" in self.canvas.gettags(item):
                is_box = True
                break
                
        if is_box:
            for i, box in enumerate(self.boxes):
                if box['id'] in current or box['text_id'] in current:
                    self.inspector_listbox.selection_clear(0, tk.END)
                    self.inspector_listbox.selection_set(i)
                    self.inspector_listbox.event_generate("<<ListboxSelect>>")
                    self.inspector_listbox.see(i)
                    break
            self.drawing_prevented = True
            return
            
        self.drawing_prevented = False
        
        self.current_box_start = (event.x, event.y)
        self.drawing_rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

    def on_canvas_drag(self, event):
        if getattr(self, 'drawing_prevented', False): return
        if self.current_box_start and self.drawing_rect_id:
            x, y = self.current_box_start
            self.canvas.coords(self.drawing_rect_id, x, y, event.x, event.y)

    def on_canvas_release(self, event):
        if getattr(self, 'drawing_prevented', False):
            self.drawing_prevented = False
            return
        if self.current_box_start and self.drawing_rect_id:
            x1, y1 = self.current_box_start
            x2, y2 = event.x, event.y
            
            # Normalize coords
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])
            
            # Check if box is big enough
            if (x2 - x1) > 5 and (y2 - y1) > 5:
                # Convert screen coords to image coords
                img_x1 = x1 / self.scale
                img_y1 = y1 / self.scale
                img_x2 = x2 / self.scale
                img_y2 = y2 / self.scale
                
                cls = self.selected_class if self.selected_class else "Unassigned"
                
                self.canvas.delete(self.drawing_rect_id) # Remove temp
                self.add_box_visual(img_x1, img_y1, img_x2, img_y2, cls, record_history=True)
            else:
                self.canvas.delete(self.drawing_rect_id)
            
            self.current_box_start = None
            self.drawing_rect_id = None

    def add_box_visual(self, x1, y1, x2, y2, cls_name, record_history=False):
        # Draw on canvas
        sx1, sy1 = x1 * self.scale, y1 * self.scale
        sx2, sy2 = x2 * self.scale, y2 * self.scale
        
        rect_id = self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline="green", width=2, tags="box")
        text_id = self.canvas.create_text(sx1, sy1-10, text=cls_name, fill="green", anchor=tk.SW, tags="box")
        
        self._bind_box(rect_id, text_id, "green")
        
        box_data = {
            'id': rect_id,
            'text_id': text_id,
            'class': cls_name,
            'bbox': [x1, y1, x2, y2]
        }
        self.boxes.append(box_data)
        self.update_inspector()
        
        if record_history:
            self.history.append(('add', box_data))
            self.redo_stack.clear()

    def update_inspector(self):
        self.inspector_listbox.delete(0, tk.END)
        for i, box in enumerate(self.boxes):
            self.inspector_listbox.insert(tk.END, f"{i}: {box['class']}")

    def on_inspector_select(self, event):
        sel = self.inspector_listbox.curselection()
        if sel:
            idx = sel[0]
            # Highlight box?
            # For now just select it for deletion
            pass

    def handle_delete_key(self, event):
        # If image listbox has focus, delete image
        if self.focus_get() == self.image_listbox:
            self.delete_current_image()
        else:
            self.delete_selected_box()

    def delete_current_image(self):
        """Delete currently selected image(s) from the image list."""
        selections = self.image_listbox.curselection()
        if not selections:
            if not self.current_image_path:
                return
            # Fallback to current image
            filename = os.path.basename(self.current_image_path)
            if messagebox.askyesno("Delete Image", f"Are you sure you want to delete {filename}?"):
                self._delete_image_file(self.current_image_path)
            return
        
        # Multi-select deletion
        count = len(selections)
        if not messagebox.askyesno("Delete Images", f"Are you sure you want to delete {count} image(s)?"):
            return
        
        # Delete all selected images
        for idx in sorted(selections, reverse=True):
            if idx < len(self.images):
                filename = self.images[idx]
                img_path = os.path.join(self.project_manager.current_project_path, "data", "images", filename)
                self._delete_image_file(img_path)
        
        self.refresh_image_list()
        
        # Select next or previous
        if self.current_image_index < len(self.images):
            self.image_listbox.selection_set(self.current_image_index)
        elif self.images:
            self.image_listbox.selection_set(len(self.images)-1)
        
        self.image_listbox.event_generate("<<ListboxSelect>>")
    
    def _delete_image_file(self, img_path):
        """Helper to delete an image and its label."""
        try:
            filename = os.path.basename(img_path)
            # Delete image
            if os.path.exists(img_path):
                os.remove(img_path)
            
            # Delete label if exists
            label_name = os.path.splitext(filename)[0] + ".txt"
            label_path = os.path.join(self.project_manager.current_project_path, "data", "labels", label_name)
            if os.path.exists(label_path):
                os.remove(label_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete {filename}: {e}")

    def on_mouse_wheel(self, event):
        classes = self.project_manager.get_classes()
        if not classes: return
        
        current_idx = -1
        if self.selected_class in classes:
            current_idx = classes.index(self.selected_class)
        
        # Windows: event.delta is usually 120 or -120
        # Linux: Button-4 is up, Button-5 is down
        delta = 0
        if event.num == 5 or event.delta < 0:
            delta = 1
        elif event.num == 4 or event.delta > 0:
            delta = -1
            
        new_idx = (current_idx + delta) % len(classes)
        self.selected_class = classes[new_idx]
        
        # Update listbox selection
        self.class_listbox.selection_clear(0, tk.END)
        self.class_listbox.selection_set(new_idx)
        self.class_listbox.see(new_idx)

    def delete_selected_box(self):
        """Delete selected box(es) from inspector."""
        selections = self.inspector_listbox.curselection()
        if not selections:
            return
        
        # Sort in reverse to delete from end to start (preserves indices)
        for idx in sorted(selections, reverse=True):
            if idx < len(self.boxes):
                box = self.boxes.pop(idx)
                self.canvas.delete(box['id'])
                self.canvas.delete(box['text_id'])
                if action_type:
                    self.history.append((action_type, box, idx))
                else:
                    self.history.append(('delete', box, idx))
        
        self.redo_stack.clear()
        self.update_inspector()

    def _bind_box(self, rect_id, text_id, color):
        self.canvas.tag_bind(rect_id, "<Enter>", lambda e, bid=rect_id, c=color: self.on_box_enter(bid, c))
        self.canvas.tag_bind(rect_id, "<Leave>", lambda e, bid=rect_id, c=color: self.on_box_leave(bid, c))
        self.canvas.tag_bind(text_id, "<Enter>", lambda e, bid=rect_id, c=color: self.on_box_enter(bid, c))
        self.canvas.tag_bind(text_id, "<Leave>", lambda e, bid=rect_id, c=color: self.on_box_leave(bid, c))

    def on_box_enter(self, bid, color):
        try:
            if self.canvas.type(bid) == "rectangle":
                self.canvas.itemconfig(bid, fill=color, stipple='gray25', width=3)
        except tk.TclError:
            pass

    def on_box_leave(self, bid, color):
        try:
            if self.canvas.type(bid) == "rectangle":
                self.canvas.itemconfig(bid, fill='', stipple='', width=2)
        except tk.TclError:
            pass

    def undo(self):
        if not self.history: return
        action = self.history.pop()
        
        if action[0] == 'add':
            box = action[1]
            self.boxes.remove(box)
            self.canvas.delete(box['id'])
            self.canvas.delete(box['text_id'])
            self.redo_stack.append(action)
        elif action[0] == 'delete':
            box = action[1]
            idx = action[2]
            self.boxes.insert(idx, box)
            # Re-create visual
            sx1, sy1 = box['bbox'][0] * self.scale, box['bbox'][1] * self.scale
            sx2, sy2 = box['bbox'][2] * self.scale, box['bbox'][3] * self.scale
            box['id'] = self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline="green", width=2, tags="box")
            box['text_id'] = self.canvas.create_text(sx1, sy1-10, text=box['class'], fill="green", anchor=tk.SW, tags="box")
            self._bind_box(box['id'], box['text_id'], "green")
            self.redo_stack.append(('delete_undo', box, idx)) # Special type for redo of undo
        
        self.update_inspector()

    def redo(self):
        if not self.redo_stack: return
        action = self.redo_stack.pop()
        
        if action[0] == 'add':
            box = action[1]
            self.add_box_visual(*box['bbox'], box['class'], record_history=False)
            # Fix history to point to new box object if needed, but here we just re-add
            self.history.append(action)
        elif action[0] == 'delete_undo':
            # This was a delete that was undone, so we redo the delete
            box = action[1]
            # Find box in list (it might be a different object if we recreated it fully, but here we kept ref)
            if box in self.boxes:
                idx = self.boxes.index(box)
                self.boxes.pop(idx)
                self.canvas.delete(box['id'])
                self.canvas.delete(box['text_id'])
                self.history.append(('delete', box, idx))

        self.update_inspector()

    def save_labels(self):
        if not self.current_image_path: return
        
        filename = os.path.basename(self.current_image_path)
        label_name = os.path.splitext(filename)[0] + ".txt"
        label_path = os.path.join(self.project_manager.current_project_path, "data", "labels", label_name)
        
        classes = self.project_manager.get_classes()
        
        with open(label_path, "w") as f:
            for box in self.boxes:
                cls_name = box['class']
                if cls_name not in classes:
                    continue # Skip unknown classes or warn
                
                cls_idx = classes.index(cls_name)
                x1, y1, x2, y2 = box['bbox']
                
                # Convert to YOLO (cx, cy, w, h) normalized
                cx = ((x1 + x2) / 2) / self.img_width
                cy = ((y1 + y2) / 2) / self.img_height
                w = (x2 - x1) / self.img_width
                h = (y2 - y1) / self.img_height
                
                f.write(f"{cls_idx} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
        
        # messagebox.showinfo("Saved", f"Labels saved for {filename}")
        self.flash_screen()
        self.next_image()

    def flash_screen(self):
        # Create a Toplevel window that covers the canvas area
        # But for simplicity and better look, let's just create a green rectangle on canvas
        # Tkinter canvas doesn't support alpha fill directly.
        # We can use a stipple pattern to simulate transparency or use a Toplevel overlay.
        
        # Using Toplevel for true transparency
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w <= 1 or h <= 1: return # Canvas not visible yet

        flash_win = tk.Toplevel(self)
        flash_win.overrideredirect(True) # No borders
        flash_win.geometry(f"{w}x{h}+{x}+{y}")
        flash_win.attributes("-alpha", 0.3)
        flash_win.configure(bg="green")
        flash_win.attributes("-topmost", True)
        
        # Destroy after 200ms
        self.after(200, flash_win.destroy)

    def next_image(self):
        if self.current_image_index < len(self.images) - 1:
            self.image_listbox.selection_clear(0, tk.END)
            self.image_listbox.selection_set(self.current_image_index + 1)
            self.image_listbox.event_generate("<<ListboxSelect>>")

    def prev_image(self):
        if self.current_image_index > 0:
            self.image_listbox.selection_clear(0, tk.END)
            self.image_listbox.selection_set(self.current_image_index - 1)
            self.image_listbox.event_generate("<<ListboxSelect>>")
