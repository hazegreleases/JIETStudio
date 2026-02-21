"""Noise addition filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class GaussianNoiseEffect(AugmentationEffect):
    """Adds Gaussian noise to simulate sensor noise."""
    
    category = FilterCategory.NOISE
    bbox_safe = True
    
    def __init__(self, var_limit_min=10.0, var_limit_max=50.0, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.var_limit_min = var_limit_min
        self.var_limit_max = var_limit_max
    
    def get_transform(self):
        return A.GaussNoise(
            var_limit=(self.var_limit_min, self.var_limit_max), 
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'var_limit_min': ParamSpec(
                value=self.var_limit_min,
                min_val=0.0,
                max_val=100.0,
                param_type='float',
                step=1.0,
                description='Minimum variance for Gaussian noise'
            ),
            'var_limit_max': ParamSpec(
                value=self.var_limit_max,
                min_val=0.0,
                max_val=100.0,
                param_type='float',
                step=1.0,
                description='Maximum variance for Gaussian noise'
            )
        }
    
    def set_params(self, params):
        if 'var_limit_min' in params:
            self.var_limit_min = float(params['var_limit_min'])
        if 'var_limit_max' in params:
            self.var_limit_max = float(params['var_limit_max'])
        # Ensure min <= max
        if self.var_limit_min > self.var_limit_max:
            self.var_limit_min, self.var_limit_max = self.var_limit_max, self.var_limit_min


class ISONoiseEffect(AugmentationEffect):
    """Adds camera ISO noise for realistic sensor simulation."""
    
    category = FilterCategory.NOISE
    bbox_safe = True
    
    def __init__(self, color_shift_min=0.01, color_shift_max=0.05, 
                 intensity_min=0.1, intensity_max=0.5, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.color_shift_min = color_shift_min
        self.color_shift_max = color_shift_max
        self.intensity_min = intensity_min
        self.intensity_max = intensity_max
    
    def get_transform(self):
        return A.ISONoise(
            color_shift=(self.color_shift_min, self.color_shift_max),
            intensity=(self.intensity_min, self.intensity_max),
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'color_shift_min': ParamSpec(
                value=self.color_shift_min,
                min_val=0.0,
                max_val=0.2,
                param_type='float',
                step=0.01,
                description='Minimum color shift variance'
            ),
            'color_shift_max': ParamSpec(
                value=self.color_shift_max,
                min_val=0.0,
                max_val=0.2,
                param_type='float',
                step=0.01,
                description='Maximum color shift variance'
            ),
            'intensity_min': ParamSpec(
                value=self.intensity_min,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Minimum noise intensity'
            ),
            'intensity_max': ParamSpec(
                value=self.intensity_max,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Maximum noise intensity'
            )
        }
    
    def set_params(self, params):
        if 'color_shift_min' in params:
            self.color_shift_min = float(params['color_shift_min'])
        if 'color_shift_max' in params:
            self.color_shift_max = float(params['color_shift_max'])
        if 'intensity_min' in params:
            self.intensity_min = float(params['intensity_min'])
        if 'intensity_max' in params:
            self.intensity_max = float(params['intensity_max'])
