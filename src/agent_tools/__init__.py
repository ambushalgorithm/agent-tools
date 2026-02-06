"""Agent Tools - Reusable utilities for AI agents."""

__version__ = "0.1.0"

# Core (always available)
from agent_tools.vision.base import VisionClient, VisionResult
from agent_tools.registry import list_tools, get_tool, discover

# Optional providers (lazy import to avoid hard dependencies)
try:
    from agent_tools.vision.venice import VeniceVisionClient
except ImportError:
    VeniceVisionClient = None  # type: ignore

try:
    from agent_tools.vision.ollama import OllamaVisionClient
except ImportError:
    OllamaVisionClient = None  # type: ignore

__all__ = [
    "VisionClient",
    "VisionResult", 
    "VeniceVisionClient",
    "OllamaVisionClient",
    "list_tools",
    "get_tool",
    "discover",
]
