"""Configuration utilities for environment-driven setup."""

import os
from pathlib import Path


def get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """Get an environment variable with optional default and required check.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        required: If True, raises ValueError when not set
        
    Returns:
        The environment variable value or default
        
    Raises:
        ValueError: If required=True and variable is not set
    """
    value = os.environ.get(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def load_dotenv(env_path: Path | None = None) -> None:
    """Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. If None, looks for .env in current directory
                 and working up to root.
    """
    if env_path is None:
        # Search upward from current directory
        current = Path.cwd()
        for path in [current] + list(current.parents):
            dotenv = path / ".env"
            if dotenv.exists():
                env_path = dotenv
                break
    
    if env_path is None or not env_path.exists():
        return
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                if key not in os.environ:  # Don't override existing
                    os.environ[key] = value
