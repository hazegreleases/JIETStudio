"""Exposure and gamma correction filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class ExposureEffect(AugmentationEffect):
    """Adjusts image exposure using gamma correction."""
    
    category = FilterCategory.COLOR
    bbox_safe = True
    
    def __init__(self, gamma_min=80, gamma_max=120, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.gamma_min = gamma_min
        self.gamma_max = gamma_max
    
    def get_transform(self):
        return A.RandomGamma(
            gamma_limit=(self.gamma_min, self.gamma_max),
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'gamma_min': ParamSpec(
                value=self.gamma_min,
                min_val=40,
                max_val=200,
                param_type='int',
                step=5,
                description='Minimum gamma value (lower = darker)'
            ),
            'gamma_max': ParamSpec(
                value=self.gamma_max,
                min_val=40,
                max_val=200,
                param_type='int',
                step=5,
                description='Maximum gamma value (higher = brighter)'
            )
        }
    
    def set_params(self, params):
        if 'gamma_min' in params:
            self.gamma_min = int(params['gamma_min'])
        if 'gamma_max' in params:
            self.gamma_max = int(params['gamma_max'])


class CLAHEEffect(AugmentationEffect):
    """
    Contrast Limited Adaptive Histogram Equalization.
    Enhances local contrast without over-amplifying noise.
    """
    
    category = FilterCategory.COLOR
    bbox_safe = True
    
    def __init__(self, clip_limit=4.0, tile_grid_size=8, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
    
    def get_transform(self):
        return A.CLAHE(
            clip_limit=self.clip_limit,
            tile_grid_size=(self.tile_grid_size, self.tile_grid_size),
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'clip_limit': ParamSpec(
                value=self.clip_limit,
                min_val=1.0,
                max_val=10.0,
                param_type='float',
                step=0.5,
                description='Threshold for contrast limiting'
            ),
            'tile_grid_size': ParamSpec(
                value=self.tile_grid_size,
                min_val=4,
                max_val=16,
                param_type='int',
                step=2,
                description='Size of grid for histogram equalization'
            )
        }
    
    def set_params(self, params):
        if 'clip_limit' in params:
            self.clip_limit = float(params['clip_limit'])
        if 'tile_grid_size' in params:
            self.tile_grid_size = int(params['tile_grid_size'])
