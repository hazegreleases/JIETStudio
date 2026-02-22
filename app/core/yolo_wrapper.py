import os
import yaml
import random
import threading
from ultralytics import YOLO
import shutil
from datetime import datetime
import gc
import torch

class YOLOWrapper:
    def __init__(self, project_path):
        self.project_path = project_path
        # Global models directory
        self.models_dir = os.path.join(os.path.expanduser("~"), ".jiet_yolo_models")
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        
        self.stop_training_flag = False
            
        self.data_dir = os.path.join(project_path, "data")
        self.images_dir = os.path.join(self.data_dir, "images")
        self.labels_dir = os.path.join(self.data_dir, "labels")

    def prepare_dataset(self, validation_split=0.2, bg_ratio=0.1):
        """Generates train.txt and val.txt with random split and BG sampling."""
        all_imgs = [f for f in os.listdir(self.images_dir) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        labeled_imgs = []
        verified_bg_imgs = []
        
        for img_file in all_imgs:
            img_path = os.path.join(self.images_dir, img_file).replace('\\', '/')
            label_file = os.path.splitext(img_file)[0] + ".txt"
            label_path = os.path.join(self.labels_dir, label_file)
            

            if os.path.exists(label_path):
                if os.path.getsize(label_path) > 0:
                    labeled_imgs.append(img_path)
                else:
                    verified_bg_imgs.append(img_path)
            # Unlabeled images (no label file) are EXCLUDED from training
        
        # Shuffle labeled
        random.shuffle(labeled_imgs)
        if validation_split > 1.0:
            validation_split = validation_split / 100.0
        split_idx = int(len(labeled_imgs) * (1 - validation_split))

        train_labeled = labeled_imgs[:split_idx]
        val_labeled = labeled_imgs[split_idx:]
        
        # Calculate BG quotas
        train_bg_count = int(len(train_labeled) * bg_ratio)
        val_bg_count = int(len(val_labeled) * bg_ratio)
        
        random.shuffle(verified_bg_imgs)
        
        train_bg = verified_bg_imgs[:train_bg_count]
        val_bg = verified_bg_imgs[train_bg_count : train_bg_count + val_bg_count]
        
        train_imgs = train_labeled + train_bg
        val_imgs = val_labeled + val_bg
        
        random.shuffle(train_imgs)
        random.shuffle(val_imgs)

        train_txt = os.path.join(self.data_dir, "train.txt").replace('\\', '/')
        val_txt = os.path.join(self.data_dir, "val.txt").replace('\\', '/')

        with open(train_txt, "w") as f:
            f.write("\n".join(train_imgs))
        
        with open(val_txt, "w") as f:
            f.write("\n".join(val_imgs))

        return train_txt, val_txt

    def generate_yaml(self, classes, train_txt, val_txt):
        """Generates a data.yaml file for training."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        yaml_path = os.path.join(self.data_dir, f"config_{timestamp}.yaml")
        
        data = {
            'path': self.data_dir,
            'train': train_txt,
            'val': val_txt,
            'names': {i: name for i, name in enumerate(classes)}
        }
        
        with open(yaml_path, "w") as f:
            yaml.dump(data, f)
        
        return yaml_path

    def stop_training(self):
        self.stop_training_flag = True
    
    def cleanup_memory(self):
        """Aggressive memory cleanup to free VRAM and RAM after training."""
        print("[Memory Cleanup] Clearing VRAM and RAM...")
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            print(f"[Memory Cleanup] Freed CUDA cache")
        
        # Additional garbage collection
        gc.collect()
        
        print("[Memory Cleanup] Memory cleanup complete")

    def train_model(self, model_name, data_yaml, epochs, batch_size, imgsz, callback=None, half=False, workers=4, resume=False, **kwargs):
        """Runs training in a separate thread."""
        self.stop_training_flag = False
        
        def on_train_epoch_end(trainer):
            if self.stop_training_flag:
                print("Training stopped by user.")
                trainer.stop = True
                raise InterruptedError("Training stopped by user.")

        def run():
            try:
                model_path = os.path.join(self.models_dir, model_name)
                if not os.path.exists(model_path) and not model_name.endswith('.pt'):
                     pass
                
                model = YOLO(model_name) 
                model.add_callback("on_train_epoch_end", on_train_epoch_end)
                
                project_runs = os.path.join(self.project_path, "runs")
                name = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                results = model.train(
                    data=data_yaml,
                    epochs=epochs,
                    batch=batch_size,
                    imgsz=imgsz,
                    project=project_runs,
                    name=name,
                    exist_ok=True,
                    workers=workers,
                    half=half,
                    resume=resume,
                    **kwargs
                )
                
                # Clean up model reference and memory
                del model
                self.cleanup_memory()
                
                if callback:
                    callback(f"Training completed. Results saved to {project_runs}/{name}")
            except InterruptedError:
                # Clean up on manual stop
                try:
                    del model
                except:
                    pass
                self.cleanup_memory()
                
                if callback:
                    callback("Training stopped by user.")
            except Exception as e:
                # Clean up on error
                try:
                    del model
                except:
                    pass
                self.cleanup_memory()
                
                if callback:
                    callback(f"Error during training: {str(e)}")

        thread = threading.Thread(target=run)
        thread.start()

    def run_inference(self, model_path, source, conf=0.25, device=None):
        """Runs inference on a source."""
        model = YOLO(model_path)
        # return results object
        # For webcam, source is int. For image, str.
        results = model.predict(source=source, conf=conf, save=False, device=device)
        return results

    def export_model(self, model_path, format="onnx"):
        """Exports the model to the specified format."""
        model = YOLO(model_path)
        export_path = model.export(format=format)
        return export_path

    def get_device_info(self):
        """Returns information about the device used for training/inference."""
        import torch
        if torch.cuda.is_available():
            return f"CUDA ({torch.cuda.get_device_name(0)})"
        elif torch.backends.mps.is_available():
            return "MPS (Apple Metal)"
        else:
            return "CPU"
