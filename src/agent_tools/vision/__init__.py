"""Vision and image analysis tools."""

from agent_tools.vision.base import VisionClient, VisionResult

# Lazy imports to avoid hard dependency on all providers
try:
    from agent_tools.vision.ollama import OllamaVisionClient
except ImportError:
    OllamaVisionClient = None  # type: ignore

try:
    from agent_tools.vision.venice import VeniceVisionClient
except ImportError:
    VeniceVisionClient = None  # type: ignore

__all__ = [
    "VisionClient",
    "VisionResult",
    "OllamaVisionClient",
    "VeniceVisionClient",
]
