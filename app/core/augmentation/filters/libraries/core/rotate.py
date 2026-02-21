"""Rotation transformation filter."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A
import cv2


class RotateEffect(AugmentationEffect):
    """Rotates image by random angle within specified range."""
    
    category = FilterCategory.GEOMETRIC
    bbox_safe = True
    
    def __init__(self, limit=15, border_value=0, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.limit = limit
        self.border_value = border_value
    
    def get_transform(self):
        return A.Rotate(
            limit=self.limit, 
            border_mode=cv2.BORDER_CONSTANT,
            value=self.border_value,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'limit': ParamSpec(
                value=self.limit,
                min_val=0,
                max_val=180,
                param_type='int',
                step=5,
                description='Maximum rotation angle in degrees (+/- limit)'
            ),
            'border_value': ParamSpec(
                value=self.border_value,
                min_val=0,
                max_val=255,
                param_type='int',
                step=1,
                description='Padding color value (0=black, 255=white)'
            )
        }
    
    def set_params(self, params):
        if 'limit' in params:
            self.limit = int(params['limit'])
        if 'border_value' in params:
            self.border_value = int(params['border_value'])


class SafeRotateEffect(AugmentationEffect):
    """Rotates only to 90-degree angles (90, 180, 270) for perfect bbox preservation."""
    
    category = FilterCategory.GEOMETRIC
    bbox_safe = True
    
    def get_transform(self):
        return A.RandomRotate90(p=self.probability)
    
    def get_param_specs(self):
        return {}  # No additional parameters
    
    def set_params(self, params):
        pass  # No parameters to set
