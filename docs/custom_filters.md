# Augmentation Filter Documentation

This guide explains how to create custom augmentation filters for Just In Enough Time Studio. The system uses a modular, plugin-based architecture allowing you to drop in new Python scripts to add effects.

## The Big Picture
Every augmentation effect is a subclass of `AugmentationEffect`. The system reads these classes from the `app/core/augmentation/filters/` directory (including subdirectories like `libraries/custom`).

To add a new filter:
1.  **Write a Python script** containing your effect class.
2.  **Import it** using the "Import Filter" button in the Augmentation tab.

## Creating a Filter

### 1. Structure
Your class must inherit from `AugmentationEffect` and implement three key methods:
- `get_transform()`: Returns the Albumentations transform object.
- `get_params()`: Returns a dictionary of current settings (for the UI).
- `set_params(params)`: Updates the settings based on the UI.

### 2. Example Template
Here is a complete example of a "Sepia" filter.

```python
from app.core.augmentation.base import AugmentationEffect
import albumentations as A

class SepiaEffect(AugmentationEffect):
    def __init__(self, probability=0.5, enabled=True):
        # Initialize base class
        super().__init__(probability, enabled)
        
        # No extra params for standard Sepia, but we could add some
        pass

    def get_transform(self):
        """
        Return the Albumentations transform.
        This is where the magic happens.
        """
        return A.ToSepia(p=self.probability)

    def get_params(self):
        """
        Return parameters to show in the UI.
        Since we have none, we return empty dict.
        """
        return {}

    def set_params(self, params):
        """
        Receive updates from UI sliders.
        """
        pass
```

### 3. Adding Parameters
If your filter has tunable parameters (like "strength" or "limit"), follow this pattern:

```python
class MyCustomBlur(AugmentationEffect):
    def __init__(self, blur_limit=7, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.blur_limit = blur_limit

    def get_transform(self):
        # Ensure blur_limit is odd for OpenCV
        limit = self.blur_limit if self.blur_limit % 2 != 0 else self.blur_limit + 1
        return A.Blur(blur_limit=limit, p=self.probability)

    def get_params(self):
        # This tells the UI to create a slider for 'blur_limit'
        # The key name must match (snake_case conventionally)
        return {'blur_limit': self.blur_limit}

    def set_params(self, params):
        # The UI sends a dict of changed values
        if 'blur_limit' in params: 
            self.blur_limit = int(params['blur_limit'])
```

## Best Practices
- **Bounding Boxes**: Uses `Albumentations` transforms that are "bbox-safe" (like `SafeCrop`, `Rotate`, `Flip`) if you are manipulating geometry. Using unsafe transforms on geometric data might break your labels!
- **Dependencies**: You can import `cv2`, `numpy`, and `albumentations` freely.
- **Naming**: Give your class a descriptive name (e.g., `SuperNoiseEffect`). The name will appear in the UI list.

## Libraries
The system organizes filters into libraries:
- `core`: Built-in essential filters.
- `custom`: User-imported filters (this is where your imports go).

You can create your own library folders inside `app/core/augmentation/filters/libraries/` if you want to organize a large collection manually.
