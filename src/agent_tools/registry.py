"""Auto-discovery registry for agent tools.

This module provides programmatic discovery of all available tools
in the package. Use it to:

1. List available tools dynamically
2. Check which tools are configured/enabled
3. Import and use tools by name

Example:
    from agent_tools.registry import list_tools, get_tool
    
    # See what's available
    for tool in list_tools():
        print(f"{tool.name}: {tool.description}")
    
    # Get a specific tool class
    OllamaVisionClient = get_tool("vision.ollama")
"""

from dataclasses import dataclass
from typing import Callable, Type, Any
from importlib import import_module


@dataclass
class ToolInfo:
    """Metadata about an available tool."""
    
    name: str  # dot-notation name, e.g., "vision.ollama"
    description: str
    module_path: str  # e.g., "agent_tools.vision.ollama"
    class_name: str
    env_vars: list[str]  # Required environment variables
    is_available: Callable[[], bool]  # Check if configured
    
    @property
    def cls(self) -> Type[Any]:
        """Dynamically import and return the tool class."""
        module = import_module(self.module_path)
        return getattr(module, self.class_name)


# Registry of all tools
_REGISTRY: list[ToolInfo] = [
    ToolInfo(
        name="vision.ollama",
        description="Ollama Cloud vision analysis (free tier, preferred)",
        module_path="agent_tools.vision.ollama",
        class_name="OllamaVisionClient",
        env_vars=["OLLAMA_HOST"],
        is_available=lambda: _check_env("OLLAMA_HOST") is not None,
    ),
    ToolInfo(
        name="vision.venice",
        description="Venice AI vision analysis (paid, reliable fallback)",
        module_path="agent_tools.vision.venice", 
        class_name="VeniceVisionClient",
        env_vars=["VENICE_API_KEY"],
        is_available=lambda: _check_env("VENICE_API_KEY") is not None,
    ),
]


def _check_env(var: str) -> str | None:
    """Check if an environment variable is set."""
    import os
    return os.environ.get(var)


def list_tools(only_available: bool = False) -> list[ToolInfo]:
    """List all registered tools.
    
    Args:
        only_available: If True, only return tools with env vars configured
        
    Returns:
        List of ToolInfo objects
    """
    if only_available:
        return [t for t in _REGISTRY if t.is_available()]
    return list(_REGISTRY)


def get_tool(name: str) -> Type[Any]:
    """Get a tool class by name.
    
    Args:
        name: Tool name in dot notation (e.g., "vision.ollama")
        
    Returns:
        The tool class
        
    Raises:
        KeyError: If tool not found
    """
    for tool in _REGISTRY:
        if tool.name == name:
            return tool.cls
    raise KeyError(f"Tool '{name}' not found. Available: {[t.name for t in _REGISTRY]}")


def get_tool_info(name: str) -> ToolInfo:
    """Get tool metadata by name.
    
    Args:
        name: Tool name in dot notation
        
    Returns:
        ToolInfo object
        
    Raises:
        KeyError: If tool not found
    """
    for tool in _REGISTRY:
        if tool.name == name:
            return tool
    raise KeyError(f"Tool '{name}' not found")


def discover() -> dict:
    """Return discovery info as serializable dict.
    
    Returns:
        Dictionary with tool info suitable for JSON serialization
    """
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "module": t.module_path,
                "class": t.class_name,
                "requires_env": t.env_vars,
                "available": t.is_available(),
            }
            for t in _REGISTRY
        ],
        "total": len(_REGISTRY),
        "available": sum(1 for t in _REGISTRY if t.is_available()),
    }
