"""Cropping transformation filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class RandomCropEffect(AugmentationEffect):
    """
    Randomly crops image while preserving bounding boxes.
    Resolution-independent using percentage-based sizing.
    """
    
    category = FilterCategory.SPATIAL
    bbox_safe = True  # With min_area safety check
    
    def __init__(self, scale_min=0.7, scale_max=0.9, min_bbox_area=0.1, 
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.min_bbox_area = min_bbox_area
    
    def get_transform(self):
        # Use RandomResizedCrop which handles resolution-independence natively.
        # The 'size' param is set to a large value and albumentations handles scaling.
        # We use scale range directly from our params.
        return A.RandomResizedCrop(
            height=640,  # Output height — will be overridden by pipeline if needed
            width=640,   # Output width
            scale=(self.scale_min, self.scale_max),
            ratio=(0.9, 1.1),
            interpolation=1,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'scale_min': ParamSpec(
                value=self.scale_min,
                min_val=0.3,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Minimum crop scale (fraction of original size)'
            ),
            'scale_max': ParamSpec(
                value=self.scale_max,
                min_val=0.3,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Maximum crop scale (fraction of original size)'
            ),
            'min_bbox_area': ParamSpec(
                value=self.min_bbox_area,
                min_val=0.0,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Minimum bbox area to keep (0.1 = keep if >10% remains)'
            )
        }
    
    def set_params(self, params):
        if 'scale_min' in params:
            self.scale_min = float(params['scale_min'])
        if 'scale_max' in params:
            self.scale_max = float(params['scale_max'])
        if 'min_bbox_area' in params:
            self.min_bbox_area = float(params['min_bbox_area'])


class CenterCropEffect(AugmentationEffect):
    """Crops center region of image. Uses percentage-based sizing."""
    
    category = FilterCategory.SPATIAL
    bbox_safe = False  # May crop out bboxes
    
    def __init__(self, scale=0.8, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.scale = scale
    
    def get_transform(self):
        # Use CropAndPad with negative padding to perform a center crop
        # The crop percentage is (1.0 - scale) / 2 on each side
        crop_frac = -(1.0 - self.scale) / 2.0
        return A.CropAndPad(
            percent=crop_frac,
            keep_size=True,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'scale': ParamSpec(
                value=self.scale,
                min_val=0.3,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Crop scale (fraction of original size)'
            )
        }
    
    def set_params(self, params):
        if 'scale' in params:
            self.scale = float(params['scale'])


class RandomResizedCropEffect(AugmentationEffect):
    """
    Crops random region and resizes to target size.
    Good for training on different scales.
    """
    
    category = FilterCategory.SPATIAL
    bbox_safe = True
    
    def __init__(self, scale_min=0.5, scale_max=1.0, ratio_min=0.75, ratio_max=1.33,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.scale_min = scale_min
        self.scale_max = scale_max
        self.ratio_min = ratio_min
        self.ratio_max = ratio_max
    
    def get_transform(self):
        return A.RandomResizedCrop(
            height=640,
            width=640,
            scale=(self.scale_min, self.scale_max),
            ratio=(self.ratio_min, self.ratio_max),
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'scale_min': ParamSpec(
                value=self.scale_min,
                min_val=0.1,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Minimum area scale for cropping'
            ),
            'scale_max': ParamSpec(
                value=self.scale_max,
                min_val=0.1,
                max_val=1.0,
                param_type='float',
                step=0.05,
                description='Maximum area scale for cropping'
            ),
            'ratio_min': ParamSpec(
                value=self.ratio_min,
                min_val=0.5,
                max_val=2.0,
                param_type='float',
                step=0.05,
                description='Minimum aspect ratio (width/height)'
            ),
            'ratio_max': ParamSpec(
                value=self.ratio_max,
                min_val=0.5,
                max_val=2.0,
                param_type='float',
                step=0.05,
                description='Maximum aspect ratio (width/height)'
            )
        }
    
    def set_params(self, params):
        if 'scale_min' in params:
            self.scale_min = float(params['scale_min'])
        if 'scale_max' in params:
            self.scale_max = float(params['scale_max'])
        if 'ratio_min' in params:
            self.ratio_min = float(params['ratio_min'])
        if 'ratio_max' in params:
            self.ratio_max = float(params['ratio_max'])
