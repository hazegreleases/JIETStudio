"""Brightness and contrast adjustment filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class BrightnessContrastEffect(AugmentationEffect):
    """Randomly adjusts brightness and contrast levels."""
    
    category = FilterCategory.COLOR
    bbox_safe = True
    
    def __init__(self, brightness_limit=0.2, contrast_limit=0.2, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.brightness_limit = brightness_limit
        self.contrast_limit = contrast_limit
    
    def get_transform(self):
        return A.RandomBrightnessContrast(
            brightness_limit=self.brightness_limit,
            contrast_limit=self.contrast_limit,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'brightness_limit': ParamSpec(
                value=self.brightness_limit,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.01,
                description='Range for brightness adjustment (-limit to +limit)'
            ),
            'contrast_limit': ParamSpec(
                value=self.contrast_limit,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.01,
                description='Range for contrast adjustment (-limit to +limit)'
            )
        }
    
    def set_params(self, params):
        if 'brightness_limit' in params:
            self.brightness_limit = float(params['brightness_limit'])
        if 'contrast_limit' in params:
            self.contrast_limit = float(params['contrast_limit'])


class BrightnessEffect(AugmentationEffect):
    """Adjusts only image brightness."""
    
    category = FilterCategory.COLOR
    bbox_safe = True
    
    def __init__(self, limit=0.2, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.limit = limit
    
    def get_transform(self):
        return A.RandomBrightnessContrast(
            brightness_limit=self.limit,
            contrast_limit=0,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'limit': ParamSpec(
                value=self.limit,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.01,
                description='Range for brightness adjustment'
            )
        }
    
    def set_params(self, params):
        if 'limit' in params:
            self.limit = float(params['limit'])


class ContrastEffect(AugmentationEffect):
    """Adjusts only image contrast."""
    
    category = FilterCategory.COLOR
    bbox_safe = True
    
    def __init__(self, limit=0.2, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.limit = limit
    
    def get_transform(self):
        return A.RandomBrightnessContrast(
            brightness_limit=0,
            contrast_limit=self.limit,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'limit': ParamSpec(
                value=self.limit,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.01,
                description='Range for contrast adjustment'
            )
        }
    
    def set_params(self, params):
        if 'limit' in params:
            self.limit = float(params['limit'])
