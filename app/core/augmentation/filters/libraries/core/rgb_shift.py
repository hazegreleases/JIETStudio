"""RGB channel shift filters."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A


class RGBShiftEffect(AugmentationEffect):
    """Randomly shifts RGB channels to simulate chromatic aberration."""
    
    category = FilterCategory.COLOR
    bbox_safe = True
    
    def __init__(self, r_shift=20, g_shift=20, b_shift=20, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.r_shift = r_shift
        self.g_shift = g_shift
        self.b_shift = b_shift
    
    def get_transform(self):
        return A.RGBShift(
            r_shift_limit=self.r_shift, 
            g_shift_limit=self.g_shift, 
            b_shift_limit=self.b_shift, 
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'r_shift': ParamSpec(
                value=self.r_shift,
                min_val=0,
                max_val=50,
                param_type='int',
                step=1,
                description='Maximum red channel shift (+/- limit)'
            ),
            'g_shift': ParamSpec(
                value=self.g_shift,
                min_val=0,
                max_val=50,
                param_type='int',
                step=1,
                description='Maximum green channel shift (+/- limit)'
            ),
            'b_shift': ParamSpec(
                value=self.b_shift,
                min_val=0,
                max_val=50,
                param_type='int',
                step=1,
                description='Maximum blue channel shift (+/- limit)'
            )
        }
    
    def set_params(self, params):
        if 'r_shift' in params:
            self.r_shift = int(params['r_shift'])
        if 'g_shift' in params:
            self.g_shift = int(params['g_shift'])
        if 'b_shift' in params:
            self.b_shift = int(params['b_shift'])


class HueSaturationEffect(AugmentationEffect):
    """Adjusts hue, saturation, and value (brightness) in HSV color space."""
    
    category = FilterCategory.COLOR
    bbox_safe = True
    
    def __init__(self, hue_shift=20, sat_shift=30, val_shift=20, probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.hue_shift = hue_shift
        self.sat_shift = sat_shift
        self.val_shift = val_shift
    
    def get_transform(self):
        return A.HueSaturationValue(
            hue_shift_limit=self.hue_shift,
            sat_shift_limit=self.sat_shift,
            val_shift_limit=self.val_shift,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'hue_shift': ParamSpec(
                value=self.hue_shift,
                min_val=0,
                max_val=180,
                param_type='int',
                step=1,
                description='Maximum hue shift in degrees'
            ),
            'sat_shift': ParamSpec(
                value=self.sat_shift,
                min_val=0,
                max_val=100,
                param_type='int',
                step=1,
                description='Maximum saturation shift'
            ),
            'val_shift': ParamSpec(
                value=self.val_shift,
                min_val=0,
                max_val=100,
                param_type='int',
                step=1,
                description='Maximum value (brightness) shift'
            )
        }
    
    def set_params(self, params):
        if 'hue_shift' in params:
            self.hue_shift = int(params['hue_shift'])
        if 'sat_shift' in params:
            self.sat_shift = int(params['sat_shift'])
        if 'val_shift' in params:
            self.val_shift = int(params['val_shift'])
