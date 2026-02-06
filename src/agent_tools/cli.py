#!/usr/bin/env python3
"""CLI tool for discovering and using agent-tools."""

import argparse
import json
import sys
from pathlib import Path


def discover_tools():
    """Discover all available tools in the package."""
    tools = []
    
    # Import and introspect
    try:
        from agent_tools import vision
        tools.append({
            "name": "vision.ollama",
            "description": "Ollama Cloud vision analysis (free, preferred)",
            "class": "OllamaVisionClient",
            "env": ["OLLAMA_HOST"],
            "example": 'OllamaVisionClient.from_env().analyze_image("img.png", "Describe")'
        })
        tools.append({
            "name": "vision.venice", 
            "description": "Venice AI vision analysis (paid fallback)",
            "class": "VeniceVisionClient",
            "env": ["VENICE_API_KEY"],
            "example": 'VeniceVisionClient.from_env().analyze_image("img.png", "Describe")'
        })
    except ImportError:
        pass
    
    return tools


def list_tools():
    """Print formatted list of available tools."""
    tools = discover_tools()
    
    print("🛠️  Available Agent Tools\n")
    print(f"Total: {len(tools)} tools\n")
    
    for tool in tools:
        print(f"📦 {tool['name']}")
        print(f"   {tool['description']}")
        print(f"   Class: {tool['class']}")
        print(f"   Requires: {', '.join(tool['env'])}")
        print(f"   Example: {tool['example']}")
        print()


def list_json():
    """Output tools as JSON for programmatic use."""
    tools = discover_tools()
    print(json.dumps(tools, indent=2))


def check_setup():
    """Check if environment is properly configured."""
    import os
    
    print("🔍 Environment Check\n")
    
    checks = {
        "OLLAMA_HOST": ("Ollama Cloud vision", "http://127.0.0.1:11434"),
        "VENICE_API_KEY": ("Venice AI vision", None),
    }
    
    all_ok = True
    for env_var, (purpose, default) in checks.items():
        value = os.environ.get(env_var)
        if value:
            display = value[:20] + "..." if len(value) > 20 else value
            print(f"  ✅ {env_var}: {display}")
            print(f"     → {purpose} ready")
        else:
            print(f"  ❌ {env_var}: not set")
            print(f"     → {purpose} unavailable")
            if default:
                print(f"     (default would be: {default})")
            all_ok = False
        print()
    
    return all_ok


def main():
    parser = argparse.ArgumentParser(
        description="Agent Tools CLI - Discover and verify available tools"
    )
    parser.add_argument(
        "command",
        choices=["list", "json", "check"],
        default="list",
        nargs="?",
        help="Command to run: list (human), json (machine), check (env verification)"
    )
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_tools()
    elif args.command == "json":
        list_json()
    elif args.command == "check":
        ok = check_setup()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
