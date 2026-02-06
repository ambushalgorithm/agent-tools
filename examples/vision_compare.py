#!/usr/bin/env python3
"""Example: Compare Venice vs Ollama for image analysis."""

import sys
from pathlib import Path

# Add src to path for example (when not installed)
src = Path(__file__).parent.parent / "src"
if src.exists():
    sys.path.insert(0, str(src))

from agent_tools.vision import OllamaVisionClient, VeniceVisionClient


def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else "/path/to/image.png"
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Describe this image in detail"
    
    print(f"Analyzing: {image_path}")
    print(f"Prompt: {prompt}")
    print("=" * 60)
    
    # Try Ollama Cloud first (free, preferred)
    try:
        print("\n[Ollama Cloud - kimi-k2.5:cloud]")
        ollama = OllamaVisionClient.from_env()
        result = ollama.analyze_image(image_path, prompt)
        print(result.description)
        print(f"\n(Model: {result.model})")
    except Exception as e:
        print(f"Ollama failed: {e}")
    
    # Fallback to Venice (paid but reliable)
    try:
        print("\n" + "=" * 60)
        print("\n[Venice AI - qwen3-vl-235b-a22b]")
        venice = VeniceVisionClient.from_env()
        result = venice.analyze_image(image_path, prompt)
        print(result.description)
        print(f"\n(Model: {result.model})")
    except Exception as e:
        print(f"Venice failed: {e}")


if __name__ == "__main__":
    main()
