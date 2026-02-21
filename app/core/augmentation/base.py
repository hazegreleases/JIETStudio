"""
Base classes for the modular augmentation system.
Enhanced with metadata, parameter specs, and validation.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional


class FilterCategory(Enum):
    """Categories for organizing augmentation filters."""
    COLOR = "Color"
    GEOMETRIC = "Geometric"
    SPATIAL = "Spatial"
    NOISE = "Noise"
    BLUR = "Blur"
    WEATHER = "Weather"
    ADVANCED = "Advanced"
    OTHER = "Other"


class ParamSpec:
    """
    Specification for an augmentation parameter.
    Defines type, range, default value, and metadata.
    """
    
    def __init__(
        self, 
        value: Any, 
        min_val: Optional[float] = None, 
        max_val: Optional[float] = None, 
        param_type: str = 'float',
        step: Optional[float] = None,
        description: str = ''
    ):
        """
        Args:
            value: Current/default value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            param_type: Type of parameter ('float', 'int', 'bool', 'string')
            step: Step size for increments (useful for sliders)
            description: Human-readable description
        """
        self.value = value
        self.min = min_val
        self.max = max_val
        self.type = param_type
        self.step = step
        self.description = description
    
    def validate(self, value: Any) -> bool:
        """Validate if a value is within acceptable range."""
        if self.type == 'float' or self.type == 'int':
            if self.min is not None and value < self.min:
                return False
            if self.max is not None and value > self.max:
                return False
        return True
    
    def clamp(self, value: Any) -> Any:
        """Clamp value to valid range."""
        if self.type == 'float' or self.type == 'int':
            if self.min is not None:
                value = max(value, self.min)
            if self.max is not None:
                value = min(value, self.max)
        
        if self.type == 'int':
            return int(value)
        elif self.type == 'float':
            return float(value)
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'value': self.value,
            'min': self.min,
            'max': self.max,
            'type': self.type,
            'step': self.step,
            'description': self.description
        }


class AugmentationEffect(ABC):
    """
    Abstract base class for all augmentation effects.
    
    Subclasses should:
    1. Set class attributes: category, bbox_safe
    2. Implement get_transform() to return Albumentations transform
    3. Implement get_param_specs() to return ParamSpec dict
    4. Implement set_params() to update parameters
    """
    
    # Class attributes (override in subclasses)
    category = FilterCategory.OTHER
    bbox_safe = True  # Whether this filter preserves bounding boxes
    
    def __init__(self, probability: float = 0.5, enabled: bool = True):
        """
        Args:
            probability: Probability of applying this effect (0.0-1.0)
            enabled: Whether this effect is active in the pipeline
        """
        self.probability = probability
        self.enabled = enabled
        self.name = self.__class__.__name__
    
    @abstractmethod
    def get_transform(self):
        """
        Return the Albumentations transform for this effect.
        
        Returns:
            albumentations.BasicTransform: The transform instance
        """
        pass
    
    @abstractmethod
    def get_param_specs(self) -> Dict[str, ParamSpec]:
        """
        Return parameter specifications for UI configuration.
        
        Returns:
            Dict[str, ParamSpec]: Dictionary mapping parameter names to specs
        """
        pass
    
    @abstractmethod
    def set_params(self, params: Dict[str, Any]):
        """
        Set parameters from UI configuration.
        
        Args:
            params: Dictionary of parameter name -> value
        """
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """
        Get current parameter values (for backward compatibility).
        
        Returns:
            Dict[str, Any]: Dictionary of parameter name -> current value
        """
        specs = self.get_param_specs()
        return {name: spec.value for name, spec in specs.items()}
    
    def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clamp parameters to acceptable ranges.
        
        Args:
            params: Dictionary of parameter name -> value
            
        Returns:
            Dict[str, Any]: Dictionary of validated/clamped parameters
        """
        specs = self.get_param_specs()
        validated = {}
        
        for name, value in params.items():
            if name in specs:
                spec = specs[name]
                if not spec.validate(value):
                    # Clamp to valid range
                    validated[name] = spec.clamp(value)
                else:
                    validated[name] = value
            else:
                # Unknown parameter, pass through
                validated[name] = value
        
        return validated
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this effect.
        
        Returns:
            Dict containing:
                - name: Effect name
                - category: FilterCategory value
                - bbox_safe: Whether effect preserves bboxes
                - description: Effect description (from docstring)
        """
        return {
            'name': self.name,
            'category': self.category.value,
            'bbox_safe': self.bbox_safe,
            'description': self.__doc__.strip() if self.__doc__ else ''
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize effect to dictionary.
        
        Returns:
            Dict containing all effect configuration
        """
        data = self.get_params()
        data['type'] = self.__class__.__name__
        data['probability'] = self.probability
        data['enabled'] = self.enabled
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Deserialize effect from dictionary.
        Typically handled by factory, but can be useful for cloning.
        
        Args:
            data: Serialized effect data
            
        Returns:
            AugmentationEffect: New instance with loaded configuration
        """
        # Basic implementation - subclasses can override if needed
        instance = cls(
            probability=data.get('probability', 0.5),
            enabled=data.get('enabled', True)
        )
        instance.set_params(data)
        return instance
