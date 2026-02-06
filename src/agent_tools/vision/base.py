"""Base interfaces for vision clients."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Union


@dataclass
class VisionResult:
    """Result of an image analysis operation."""
    
    description: str
    raw_response: dict | None = None
    model: str | None = None
    
    def __str__(self) -> str:
        return self.description


class VisionClient(ABC):
    """Abstract base class for vision/image analysis clients."""
    
    @abstractmethod
    def analyze_image(
        self, 
        image_path: Union[str, Path],
        prompt: str,
        **kwargs
    ) -> VisionResult:
        """Analyze an image and return the result.
        
        Args:
            image_path: Path to the image file
            prompt: Prompt/instruction for the analysis
            **kwargs: Provider-specific options (model, max_tokens, etc.)
            
        Returns:
            VisionResult containing the description and metadata
        """
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def from_env(cls) -> "VisionClient":
        """Create a client instance from environment variables."""
        raise NotImplementedError
