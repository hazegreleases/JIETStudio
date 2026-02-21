"""Blur filters using Albumentations."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class BlurEffect(AugmentationEffect):
    """Applies blur to reduce image sharpness and detail."""
    
    category = FilterCategory.BLUR
    bbox_safe = True
    
    def __init__(self, blur_limit=7, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.blur_limit = blur_limit
    
    def get_transform(self):
        # blur_limit must be odd
        limit = self.blur_limit if self.blur_limit % 2 != 0 else self.blur_limit + 1
        return A.Blur(blur_limit=limit, p=self.probability)
    
    def get_param_specs(self):
        return {
            'blur_limit': ParamSpec(
                value=self.blur_limit,
                min_val=3,
                max_val=21,
                param_type='int',
                step=2,
                description='Maximum kernel size for blur (must be odd)'
            )
        }
    
    def set_params(self, params):
        if 'blur_limit' in params:
            val = int(params['blur_limit'])
            self.blur_limit = val if val % 2 != 0 else val + 1


class GaussianBlurEffect(AugmentationEffect):
    """Applies Gaussian blur for a more natural blur effect."""
    
    category = FilterCategory.BLUR
    bbox_safe = True
    
    def __init__(self, blur_limit=7, sigma_limit_min=0, sigma_limit_max=0, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.blur_limit = blur_limit
        self.sigma_limit_min = sigma_limit_min
        self.sigma_limit_max = sigma_limit_max
    
    def get_transform(self):
        limit = self.blur_limit if self.blur_limit % 2 != 0 else self.blur_limit + 1
        sigma = (self.sigma_limit_min, self.sigma_limit_max) if self.sigma_limit_max > 0 else (0.1, 2.0)
        return A.GaussianBlur(blur_limit=limit, sigma_limit=sigma, p=self.probability)
    
    def get_param_specs(self):
        return {
            'blur_limit': ParamSpec(
                value=self.blur_limit,
                min_val=3,
                max_val=21,
                param_type='int',
                step=2,
                description='Maximum kernel size for Gaussian blur'
            ),
            'sigma_limit_min': ParamSpec(
                value=self.sigma_limit_min,
                min_val=0,
                max_val=10,
                param_type='float',
                step=0.1,
                description='Minimum sigma for Gaussian kernel (0=auto)'
            ),
            'sigma_limit_max': ParamSpec(
                value=self.sigma_limit_max,
                min_val=0,
                max_val=10,
                param_type='float',
                step=0.1,
                description='Maximum sigma for Gaussian kernel (0=auto)'
            )
        }
    
    def set_params(self, params):
        if 'blur_limit' in params:
            val = int(params['blur_limit'])
            self.blur_limit = val if val % 2 != 0 else val + 1
        if 'sigma_limit_min' in params:
            self.sigma_limit_min = float(params['sigma_limit_min'])
        if 'sigma_limit_max' in params:
            self.sigma_limit_max = float(params['sigma_limit_max'])


class MotionBlurEffect(AugmentationEffect):
    """Applies motion blur to simulate camera movement."""
    
    category = FilterCategory.BLUR
    bbox_safe = True
    
    def __init__(self, blur_limit=7, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.blur_limit = blur_limit
    
    def get_transform(self):
        return A.MotionBlur(blur_limit=self.blur_limit, p=self.probability)
    
    def get_param_specs(self):
        return {
            'blur_limit': ParamSpec(
                value=self.blur_limit,
                min_val=3,
                max_val=21,
                param_type='int',
                step=2,
                description='Maximum kernel size for motion blur'
            )
        }
    
    def set_params(self, params):
        if 'blur_limit' in params:
            val = int(params['blur_limit'])
            self.blur_limit = val if val % 2 != 0 else val + 1
