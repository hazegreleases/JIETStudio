import os
import cv2
import numpy as np
from ultralytics import SAM
from PIL import Image

class SAMWrapper:
    def __init__(self, model_path="sam2.1_l.pt", device=None):
        """
        Initialize the SAM wrapper.
        
        Args:
            model_path (str): Path to the SAM model file.
            device (str): Device to run inference on ('cuda' or 'cpu'). None = auto.
        """
        self.model_path = model_path
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        """Loads the SAM model."""
        try:
            # Check if model exists locally, if not lets hope ultralytics handles it or user provided path
            if not os.path.exists(self.model_path):
                 # Try to check in global standard location if not absolute path
                 global_models = os.path.join(os.path.expanduser("~"), ".jiet_yolo_models")
                 potential_path = os.path.join(global_models, os.path.basename(self.model_path))
                 if os.path.exists(potential_path):
                     self.model_path = potential_path
            
            self.model = SAM(self.model_path)
            
            # Force device if specified (Ultralytics SAM might auto-load, but we can move it?)
            if self.device:
                # SAM wrapper from ultralytics usually puts model on device during predict or we can verify
                pass # Ultralytics typically handles device in predict() or auto-detects.
                     # But we can try to force it if possible, or just pass device to predict.
                     
            print(f"SAM Model loaded from {self.model_path}")
        except Exception as e:
            print(f"Failed to load SAM model: {e}")
            self.model = None

    def predict_point(self, image_path, point):
        """
        Run SAM prediction based on a single point.
        
        Args:
            image_path (str): Path to the image file.
            point (tuple): (x, y) coordinates of the click.
            
        Returns:
            list: [x1, y1, x2, y2] bounding box coordinates, or None if failed.
        """
        if not self.model:
            self._load_model()
            if not self.model:
                return None
        
        try:
            # Ultralytics SAM predict supports points
            # points=[[x, y]] labels=[1] (1 for foreground)
            
            # Note: Ultralytics SAM API might slightly differ between versions, 
            # ensuring generic support.
            # Convert point to list of list as expected by some interfaces
            
            results = self.model.predict(
                source=image_path,
                points=[point],
                labels=[1],
                save=False,
                device=self.device
            )
            
            if not results:
                return None
                
            # Result usually contains masks. We need the bounding box of the mask.
            # Results object -> masks -> xyxy
            
            r = results[0]
            
            # 1. Try generic boxes if available (SAM usually returns them)
            if r.boxes is not None and len(r.boxes) > 0:
                 return r.boxes.xyxy[0].tolist()
            
            # 2. Derive from masks if no boxes
            if r.masks is not None:
                 # r.masks.xy is a list of np arrays (segments)
                 # We take the first one
                 segments = r.masks.xy
                 if len(segments) > 0:
                     poly = segments[0] # numpy array (N, 2)
                     if len(poly) > 0:
                         x1 = poly[:, 0].min()
                         y1 = poly[:, 1].min()
                         x2 = poly[:, 0].max()
                         y2 = poly[:, 1].max()
                         return [float(x1), float(y1), float(x2), float(y2)]
            
            return None

        except Exception as e:
            print(f"SAM Inference error: {e}")
            return None

    def predict_box(self, image_path, box):
        """
        Run SAM prediction based on a bounding box.
        
        Args:
            image_path (str): Path to the image file.
            box (list): [x1, y1, x2, y2] coordinates of the bounding box.
            
        Returns:
            list: [x1, y1, x2, y2] bounding box coordinates of the segmentation, or None.
        """
        if not self.model:
            self._load_model()
            if not self.model:
                return None
        
        try:
            results = self.model.predict(
                source=image_path,
                bboxes=[box],
                save=False,
                device=self.device
            )
            
            if not results:
                return None
                
            r = results[0]
            
            if r.boxes is not None and len(r.boxes) > 0:
                 return r.boxes.xyxy[0].tolist()
            
            if r.masks is not None:
                 segments = r.masks.xy
                 if len(segments) > 0:
                     poly = segments[0] # numpy array (N, 2)
                     if len(poly) > 0:
                         x1 = poly[:, 0].min()
                         y1 = poly[:, 1].min()
                         x2 = poly[:, 0].max()
                         y2 = poly[:, 1].max()
                         return [float(x1), float(y1), float(x2), float(y2)]
            
            return None

        except Exception as e:
            print(f"SAM Inference error: {e}")
            return None
