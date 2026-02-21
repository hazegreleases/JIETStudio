"""Advanced geometric transformation filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class PerspectiveEffect(AugmentationEffect):
    """
    Applies perspective transformation for realistic viewing angle changes.
    Useful for training object detection with different camera angles.
    """
    
    category = FilterCategory.ADVANCED
    bbox_safe = True
    
    def __init__(self, scale=0.05, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.scale = scale
    
    def get_transform(self):
        return A.Perspective(
            scale=self.scale,
            keep_size=True,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'scale': ParamSpec(
                value=self.scale,
                min_val=0.0,
                max_val=0.2,
                param_type='float',
                step=0.01,
                description='Standard deviation of perspective distortion'
            )
        }
    
    def set_params(self, params):
        if 'scale' in params:
            self.scale = float(params['scale'])


class ElasticTransformEffect(AugmentationEffect):
    """
    Applies elastic deformation for robustness to local distortions.
    Often used in medical imaging and OCR.
    """
    
    category = FilterCategory.ADVANCED
    bbox_safe = True
    
    def __init__(self, alpha=1.0, sigma=50.0, alpha_affine=50.0,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.alpha = alpha
        self.sigma = sigma
        self.alpha_affine = alpha_affine
    
    def get_transform(self):
        return A.ElasticTransform(
            alpha=self.alpha,
            sigma=self.sigma,
            alpha_affine=self.alpha_affine,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'alpha': ParamSpec(
                value=self.alpha,
                min_val=0.0,
                max_val=5.0,
                param_type='float',
                step=0.1,
                description='Scaling factor for deformation'
            ),
            'sigma': ParamSpec(
                value=self.sigma,
                min_val=10.0,
                max_val=100.0,
                param_type='float',
                step=5.0,
                description='Smoothness of deformation (Gaussian sigma)'
            ),
            'alpha_affine': ParamSpec(
                value=self.alpha_affine,
                min_val=0.0,
                max_val=100.0,
                param_type='float',
                step=5.0,
                description='Range for affine transformation'
            )
        }
    
    def set_params(self, params):
        if 'alpha' in params:
            self.alpha = float(params['alpha'])
        if 'sigma' in params:
            self.sigma = float(params['sigma'])
        if 'alpha_affine' in params:
            self.alpha_affine = float(params['alpha_affine'])


class GridDistortionEffect(AugmentationEffect):
    """Applies grid-based distortion for wavy/ripple effects."""
    
    category = FilterCategory.ADVANCED
    bbox_safe = True
    
    def __init__(self, num_steps=5, distort_limit=0.3, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.num_steps = num_steps
        self.distort_limit = distort_limit
    
    def get_transform(self):
        return A.GridDistortion(
            num_steps=self.num_steps,
            distort_limit=self.distort_limit,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'num_steps': ParamSpec(
                value=self.num_steps,
                min_val=1,
                max_val=10,
                param_type='int',
                step=1,
                description='Number of grid cells on each side'
            ),
            'distort_limit': ParamSpec(
                value=self.distort_limit,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Maximum distortion strength'
            )
        }
    
    def set_params(self, params):
        if 'num_steps' in params:
            self.num_steps = int(params['num_steps'])
        if 'distort_limit' in params:
            self.distort_limit = float(params['distort_limit'])


class OpticalDistortionEffect(AugmentationEffect):
    """Simulates lens distortion (barrel/pincushion effects)."""
    
    category = FilterCategory.ADVANCED
    bbox_safe = True
    
    def __init__(self, distort_limit=0.5, shift_limit=0.5, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.distort_limit = distort_limit
        self.shift_limit = shift_limit
    
    def get_transform(self):
        return A.OpticalDistortion(
            distort_limit=self.distort_limit,
            shift_limit=self.shift_limit,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'distort_limit': ParamSpec(
                value=self.distort_limit,
                min_val=0.0,
                max_val=2.0,
                param_type='float',
                step=0.1,
                description='Lens distortion strength'
            ),
            'shift_limit': ParamSpec(
                value=self.shift_limit,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Center shift limit'
            )
        }
    
    def set_params(self, params):
        if 'distort_limit' in params:
            self.distort_limit = float(params['distort_limit'])
        if 'shift_limit' in params:
            self.shift_limit = float(params['shift_limit'])
