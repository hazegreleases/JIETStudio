"""Weather and environmental effects."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A

class RandomRainEffect(AugmentationEffect):
    """Adds rain effects to the image."""
    
    category = FilterCategory.WEATHER
    bbox_safe = True
    
    def __init__(self, slant_lower=-10, slant_upper=10, 
                 drop_length=20, drop_width=1,
                 drop_color_r=200, drop_color_g=200, drop_color_b=200,
                 blur_value=3, brightness_coefficient=0.7,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.slant_lower = slant_lower
        self.slant_upper = slant_upper
        self.drop_length = drop_length
        self.drop_width = drop_width
        self.drop_color = (drop_color_r, drop_color_g, drop_color_b)
        self.blur_value = blur_value
        self.brightness_coefficient = brightness_coefficient

    def get_transform(self):
        blur_val = self.blur_value if self.blur_value % 2 != 0 else self.blur_value + 1
        return A.RandomRain(
            slant_lower=self.slant_lower,
            slant_upper=self.slant_upper,
            drop_length=self.drop_length,
            drop_width=self.drop_width,
            drop_color=self.drop_color,
            blur_value=blur_val,
            brightness_coefficient=self.brightness_coefficient,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'brightness_coefficient': ParamSpec(self.brightness_coefficient, 0.0, 1.0, 'float', 0.05, 'Rain darkening effect'),
            'blur_value': ParamSpec(self.blur_value, 1, 7, 'int', 1, 'Rain blur (must be odd)')
        }
    
    def set_params(self, params):
        if 'brightness_coefficient' in params: self.brightness_coefficient = float(params['brightness_coefficient'])
        if 'blur_value' in params:
            val = int(params['blur_value'])
            self.blur_value = val if val % 2 != 0 else val + 1


class RandomFogEffect(AugmentationEffect):
    """Adds fog effects to the image."""
    
    category = FilterCategory.WEATHER
    bbox_safe = True
    
    def __init__(self, fog_coef_lower=0.3, fog_coef_upper=1.0, alpha_coef=0.08,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.fog_coef_lower = fog_coef_lower
        self.fog_coef_upper = fog_coef_upper
        self.alpha_coef = alpha_coef
    
    def get_transform(self):
        return A.RandomFog(
            fog_coef_lower=self.fog_coef_lower,
            fog_coef_upper=self.fog_coef_upper,
            alpha_coef=self.alpha_coef,
            p=self.probability
        )

    def get_param_specs(self):
        return {
            'alpha_coef': ParamSpec(self.alpha_coef, 0.0, 1.0, 'float', 0.01, 'Fog intensity')
        }

    def set_params(self, params):
        if 'alpha_coef' in params: self.alpha_coef = float(params['alpha_coef'])


class RandomSunFlareEffect(AugmentationEffect):
    """Adds sun flare effects."""
    
    category = FilterCategory.WEATHER
    bbox_safe = True
    
    def __init__(self, flare_roi_x_min=0, flare_roi_y_min=0, 
                 flare_roi_x_max=1, flare_roi_y_max=0.5,
                 angle_lower=0, angle_upper=1,
                 num_flare_circles_lower=6, num_flare_circles_upper=10,
                 src_radius=400, src_color_r=255, src_color_g=255, src_color_b=255,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.flare_roi = (flare_roi_x_min, flare_roi_y_min, flare_roi_x_max, flare_roi_y_max)
        self.angle_lower = angle_lower
        self.angle_upper = angle_upper
        self.num_flare_circles_lower = num_flare_circles_lower
        self.num_flare_circles_upper = num_flare_circles_upper
        self.src_radius = src_radius
        self.src_color = (src_color_r, src_color_g, src_color_b)
    
    def get_transform(self):
        return A.RandomSunFlare(
            flare_roi=self.flare_roi,
            angle_lower=self.angle_lower,
            angle_upper=self.angle_upper,
            num_flare_circles_lower=self.num_flare_circles_lower,
            num_flare_circles_upper=self.num_flare_circles_upper,
            src_radius=self.src_radius,
            src_color=self.src_color,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'src_radius': ParamSpec(self.src_radius, 100, 800, 'int', 50, 'Source flare radius'),
            'angle_upper': ParamSpec(self.angle_upper, 0.0, 1.0, 'float', 0.1, 'Max flare angle')
        }

    def set_params(self, params):
        if 'src_radius' in params: self.src_radius = int(params['src_radius'])
        if 'angle_upper' in params: self.angle_upper = float(params['angle_upper'])
