"""Sharpening filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class SharpenEffect(AugmentationEffect):
    """Sharpens image to enhance edges and details."""
    
    category = FilterCategory.BLUR  # Opposite of blur, but same category
    bbox_safe = True
    
    def __init__(self, alpha_min=0.2, alpha_max=0.5, lightness_min=0.5, lightness_max=1.0,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.lightness_min = lightness_min
        self.lightness_max = lightness_max
    
    def get_transform(self):
        return A.Sharpen(
            alpha=(self.alpha_min, self.alpha_max),
            lightness=(self.lightness_min, self.lightness_max),
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'alpha_min': ParamSpec(
                value=self.alpha_min,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Minimum blend factor (0=original, 1=sharp)'
            ),
            'alpha_max': ParamSpec(
                value=self.alpha_max,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Maximum blend factor'
            ),
            'lightness_min': ParamSpec(
                value=self.lightness_min,
                min_val=0.0,
                max_val=2.0,
                param_type='float',
                step=0.1,
                description='Minimum lightness adjustment'
            ),
            'lightness_max': ParamSpec(
                value=self.lightness_max,
                min_val=0.0,
                max_val=2.0,
                param_type='float',
                step=0.1,
                description='Maximum lightness adjustment'
            )
        }
    
    def set_params(self, params):
        if 'alpha_min' in params:
            self.alpha_min = float(params['alpha_min'])
        if 'alpha_max' in params:
            self.alpha_max = float(params['alpha_max'])
        if 'lightness_min' in params:
            self.lightness_min = float(params['lightness_min'])
        if 'lightness_max' in params:
            self.lightness_max = float(params['lightness_max'])
        # Ensure min <= max
        if self.alpha_min > self.alpha_max:
            self.alpha_min, self.alpha_max = self.alpha_max, self.alpha_min
        if self.lightness_min > self.lightness_max:
            self.lightness_min, self.lightness_max = self.lightness_max, self.lightness_min


class UnsharpMaskEffect(AugmentationEffect):
    """Applies unsharp masking for professional sharpening."""
    
    category = FilterCategory.BLUR
    bbox_safe = True
    
    def __init__(self, blur_limit=7, sigma_limit=0.0, alpha=0.2, threshold=10,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.blur_limit = blur_limit
        self.sigma_limit = sigma_limit
        self.alpha = alpha
        self.threshold = threshold
    
    def get_transform(self):
        return A.UnsharpMask(
            blur_limit=self.blur_limit,
            sigma_limit=self.sigma_limit,
            alpha=self.alpha,
            threshold=self.threshold,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'blur_limit': ParamSpec(
                value=self.blur_limit,
                min_val=3,
                max_val=21,
                param_type='int',
                step=2,
                description='Kernel size for Gaussian blur'
            ),
            'alpha': ParamSpec(
                value=self.alpha,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Sharpening strength'
            ),
            'threshold': ParamSpec(
                value=self.threshold,
                min_val=0,
                max_val=255,
                param_type='int',
                step=5,
                description='Threshold for edge detection'
            )
        }
    
    def set_params(self, params):
        if 'blur_limit' in params:
            self.blur_limit = int(params['blur_limit'])
        if 'alpha' in params:
            self.alpha = float(params['alpha'])
        if 'threshold' in params:
            self.threshold = int(params['threshold'])
