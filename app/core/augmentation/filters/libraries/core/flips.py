"""Flip transformation filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class HorizontalFlipEffect(AugmentationEffect):
    """Flips image horizontally (left to right)."""
    
    category = FilterCategory.GEOMETRIC
    bbox_safe = True
    
    def get_transform(self):
        return A.HorizontalFlip(p=self.probability)
    
    def get_param_specs(self):
        return {}  # No additional parameters
    
    def set_params(self, params):
        pass  # No parameters to set


class VerticalFlipEffect(AugmentationEffect):
    """Flips image vertically (top to bottom)."""
    
    category = FilterCategory.GEOMETRIC
    bbox_safe = True
    
    def get_transform(self):
        return A.VerticalFlip(p=self.probability)
    
    def get_param_specs(self):
        return {}  # No additional parameters
    
    def set_params(self, params):
        pass  # No parameters to set
