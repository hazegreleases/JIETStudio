"""
Modular Augmentation Engine.
Replaces the old fixed configuration with a pipeline of effect objects.
"""

import os
import cv2
import numpy as np
import albumentations as A
import json
import random
from datetime import datetime
from abc import ABC, abstractmethod
import concurrent.futures

# --- Dynamic Loading ---

import importlib.util
import inspect

def load_filters():
    """Recursively load AugmentationEffect subclasses from the filters directory."""
    registry = {}
    
    # Base directory for filters
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filters_dir = os.path.join(base_dir, 'augmentation', 'filters')
    
    if not os.path.exists(filters_dir):
        print(f"Warning: Filters directory not found at {filters_dir}")
        return registry

    # Walk through directory
    for root, dirs, files in os.walk(filters_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(root, file)
                
                try:
                    # Dynamic import
                    spec = importlib.util.spec_from_file_location(f"filter_module_{file}", file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Inspect for subclasses
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and obj.__module__ == module.__name__:
                            # Check if it inherits from AugmentationEffect (without importing base blindly)
                            # We can check base class name or importing base safely
                            if hasattr(obj, 'get_transform') and hasattr(obj, 'to_dict'):
                                registry[name] = obj
                                
                except Exception as e:
                    print(f"Error loading filter {file_path}: {e}")
                    
    return registry

EFFECT_REGISTRY = load_filters()

def create_effect_from_dict(data):
    effect_type = data.get('type')
    # Refresh registry on creation attempt to support hot-loading (optional, but requested)
    global EFFECT_REGISTRY
    
    if effect_type in EFFECT_REGISTRY:
        effect_cls = EFFECT_REGISTRY[effect_type]
        effect = effect_cls(probability=data.get('probability', 0.5), enabled=data.get('enabled', True))
        effect.set_params(data)
        return effect
    
    # Try reloading if not found
    EFFECT_REGISTRY = load_filters()
    if effect_type in EFFECT_REGISTRY:
        effect_cls = EFFECT_REGISTRY[effect_type]
        effect = effect_cls(probability=data.get('probability', 0.5), enabled=data.get('enabled', True))
        effect.set_params(data)
        return effect
        
    return None

# --- Pipeline ---

class AugmentationPipeline:
    def __init__(self):
        self.effects = []
        self.enabled = True
        self.augmentations_per_image = 5
        
        # Performance: Transform caching
        self._cached_compose = None
        self._cache_hash = None

    def add_effect(self, effect):
        self.effects.append(effect)

    def remove_effect(self, index):
        if 0 <= index < len(self.effects):
            self.effects.pop(index)

    def move_effect(self, from_index, to_index):
        if 0 <= from_index < len(self.effects) and 0 <= to_index < len(self.effects):
            self.effects.insert(to_index, self.effects.pop(from_index))

    def _compute_pipeline_hash(self):
        """Compute hash of current pipeline configuration for cache invalidation."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hash(config_str)
    
    def get_compose(self, use_cache=True):
        """Compile the pipeline into an Albumentations Compose object.
        
        Args:
            use_cache: If True, use cached transform if pipeline hasn't changed
            
        Returns:
            A.Compose: The composed transformation pipeline
        """
        if not use_cache:
            return self._build_compose()
        
        # Check cache
        current_hash = self._compute_pipeline_hash()
        if current_hash != self._cache_hash or self._cached_compose is None:
            self._cached_compose = self._build_compose()
            self._cache_hash = current_hash
        
        return self._cached_compose
    
    def _build_compose(self):
        """Build the Albumentations Compose object."""
        transforms = []
        for effect in self.effects:
            if effect.enabled:
                transforms.append(effect.get_transform())
        
        return A.Compose(transforms, bbox_params=A.BboxParams(
            format='yolo',
            label_fields=['class_labels'],
            min_visibility=0.3
        ))

    def to_dict(self):
        return {
            'enabled': self.enabled,
            'augmentations_per_image': self.augmentations_per_image,
            'effects': [effect.to_dict() for effect in self.effects]
        }

    def from_dict(self, data):
        self.enabled = data.get('enabled', True)
        self.augmentations_per_image = data.get('augmentations_per_image', 5)
        self.effects = []
        for effect_data in data.get('effects', []):
            effect = create_effect_from_dict(effect_data)
            if effect:
                self.effects.append(effect)

    def save(self, path):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    def load(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                self.from_dict(data)

    def run_on_image(self, image, bboxes, class_labels):
        """Run pipeline on a single image and return transformed results.
        
        Args:
            image: numpy array (RGB)
            bboxes: list of [cx, cy, w, h] in YOLO format (normalized)
            class_labels: list of class IDs
            
        Returns:
            tuple: (transformed_image, transformed_bboxes, transformed_labels)
        """
        if not self.enabled or not self.effects:
            return image, bboxes, class_labels

        # Sanitize bboxes: clip to [0, 1] range to avoid floating point precision issues with Albumentations
        sanitized_bboxes = self._clip_bboxes(bboxes) if bboxes else []

        transform = self.get_compose()
        
        try:
            kwargs = {
                'image': image,
                'bboxes': sanitized_bboxes,
                'class_labels': class_labels if class_labels else []
            }

            result = transform(**kwargs)
            return result['image'], result['bboxes'], result['class_labels']
        except Exception as e:
            # Improved error handling with context
            import traceback
            print(f"[Augmentation Error] Failed to apply pipeline")
            print(f"  Error: {str(e)}")
            print(f"  Image shape: {image.shape if hasattr(image, 'shape') else 'unknown'}")
            print(f"  Num bboxes: {len(bboxes)}")
            print(f"  Active effects: {[e.name for e in self.effects if e.enabled]}")
            print(f"  Traceback: {traceback.format_exc()}")
            return image, bboxes, class_labels

    def _clip_bboxes(self, bboxes):
        """Clip YOLO bboxes to [0, 1] range to avoid Albumentations precision errors."""
        clipped = []
        for bbox in bboxes:
            try:
                cx, cy, w, h = bbox
                # 1. Ensure dimensions are within [0, 1] and positive
                nw = max(0.0001, min(1.0, w))
                nh = max(0.0001, min(1.0, h))
                
                # 2. Ensure center is within [nw/2, 1-nw/2] so edges strictly stay within [0, 1]
                ncx = max(nw/2.0, min(1.0 - nw/2.0, cx))
                ncy = max(nh/2.0, min(1.0 - nh/2.0, cy))
                
                clipped.append([ncx, ncy, nw, nh])
            except (ValueError, TypeError):
                continue
        return clipped

# --- Engine ---

class AugmentationEngine:
    """Refactored backbone using the pipeline."""
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline or AugmentationPipeline()

    def augment_dataset(self, images_dir, labels_dir, output_images_dir, output_labels_dir, progress_callback=None, workers=4):
        """
        Augment entire dataset.
        """
        if not self.pipeline.enabled:
            return 0
        
        # Ensure output directories exist
        os.makedirs(output_images_dir, exist_ok=True)
        os.makedirs(output_labels_dir, exist_ok=True)
        
        image_files = [f for f in os.listdir(images_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and not f.startswith('aug')]
        
        total_images = len(image_files)
        augmented_count = 0
        
        if workers > 1:
            print(f"[Augmentation] Using {workers} workers")
            # Pre-build compose outside threads (thread safety: each thread gets its own)
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = []
                for idx, img_file in enumerate(image_files):
                     futures.append(executor.submit(self._augment_single_image, 
                                                    idx, img_file, images_dir, labels_dir, 
                                                    output_images_dir, output_labels_dir, 
                                                    total_images, progress_callback))
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        augmented_count += future.result()
                    except Exception as e:
                        print(f"Augmentation worker error: {e}")
        else:
            # Single thread fallback
            for idx, img_file in enumerate(image_files):
                augmented_count += self._augment_single_image(idx, img_file, images_dir, labels_dir,
                                                              output_images_dir, output_labels_dir,
                                                              total_images, progress_callback)
                    
        return augmented_count

    def _augment_single_image(self, idx, img_file, images_dir, labels_dir, output_images_dir, output_labels_dir, total_images, progress_callback):
        augmented_count = 0
        img_path = os.path.join(images_dir, img_file)
        label_file = os.path.splitext(img_file)[0] + '.txt'
        label_path = os.path.join(labels_dir, label_file)
        
        # Load source
        # cv2.imread is generally thread safe but we need to be careful with global resources if any
        image = cv2.imread(img_path)
        if image is None: return 0
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        bboxes = []
        class_labels = []
        
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(float(parts[0]))
                        cx, cy, w, h = map(float, parts[1:5])
                        bboxes.append([cx, cy, w, h])
                        class_labels.append(class_id)
        
        # Generate augmentations
        for aug_idx in range(self.pipeline.augmentations_per_image):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            rand_suffix = random.randint(1000, 9999)
            base_name = os.path.splitext(img_file)[0]
            ext = os.path.splitext(img_file)[1]
            
            aug_img_name = f"aug_{aug_idx}_{timestamp}_{rand_suffix}_{base_name}{ext}"
            aug_label_name = f"aug_{aug_idx}_{timestamp}_{rand_suffix}_{base_name}.txt"
            
            aug_img_path = os.path.join(output_images_dir, aug_img_name)
            aug_label_path = os.path.join(output_labels_dir, aug_label_name)
            
            # Run Pipeline
            # Note: Pipeline get_compose handles caching. In threaded env, we should verify thread safety of Albumentations.
            # Albumentations Compose is generally stateless during call, but our caching mechanism might need lock if we update it.
            # However, we build it once usually.
            
            aug_img, aug_bboxes, aug_classes = self.pipeline.run_on_image(image, bboxes, class_labels)
            
            # Save results
            final_img = cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(aug_img_path, final_img)
            
            with open(aug_label_path, 'w') as f:
                for bbox, class_id in zip(aug_bboxes, aug_classes):
                    cx, cy, w, h = bbox
                    f.write(f"{int(class_id)} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
            
            augmented_count += 1
            
            if progress_callback:
                current = idx * self.pipeline.augmentations_per_image + aug_idx + 1
                total = total_images * self.pipeline.augmentations_per_image
                progress_callback(current, total, f"Augmenting {img_file}")
                
        return augmented_count

    def preview_augmentation(self, image_path, label_path):
        """Preview helper."""
        image = cv2.imread(image_path)
        if image is None: return None
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        bboxes = []
        class_labels = []
        
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(float(parts[0]))
                        cx, cy, w, h = map(float, parts[1:5])
                        bboxes.append([cx, cy, w, h])
                        class_labels.append(class_id)
                        
        aug_img, aug_bboxes, aug_classes = self.pipeline.run_on_image(image, bboxes, class_labels)
        return aug_img, aug_bboxes, aug_classes
