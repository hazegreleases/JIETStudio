"""Compression and quality reduction effects."""

from app.core.augmentation.base import AugmentationEffect, ParamSpec, FilterCategory
import albumentations as A

class ImageCompressionEffect(AugmentationEffect):
    """Simulates image compression artifacts (JPEG/WebP)."""
    
    category = FilterCategory.NOISE
    bbox_safe = True
    
    def __init__(self, quality_lower=50, quality_upper=100, compression_type=0,
                 probability=0.5, enabled=True):
        super().__init__(probability, enabled)
        self.quality_lower = quality_lower
        self.quality_upper = quality_upper
        self.compression_type = compression_type # 0: JPEG, 1: WebP
        
    def get_transform(self):
        return A.ImageCompression(
            quality_lower=self.quality_lower,
            quality_upper=self.quality_upper,
            compression_type=self.compression_type,
            p=self.probability
        )
    
    def get_param_specs(self):
        return {
            'quality_lower': ParamSpec(self.quality_lower, 1, 100, 'int', 5, 'Min Quality'),
            'quality_upper': ParamSpec(self.quality_upper, 1, 100, 'int', 5, 'Max Quality'),
            'compression_type': ParamSpec(self.compression_type, 0, 1, 'int', 1, 'Type (0=JPEG, 1=WebP)')
        }

    def set_params(self, params):
        if 'quality_lower' in params: self.quality_lower = int(params['quality_lower'])
        if 'quality_upper' in params: self.quality_upper = int(params['quality_upper'])
        if 'compression_type' in params: self.compression_type = int(params['compression_type'])
        # Ensure quality_lower <= quality_upper to prevent Albumentations crash
        if self.quality_lower > self.quality_upper:
            self.quality_lower, self.quality_upper = self.quality_upper, self.quality_lower
