"""Ollama Cloud vision client implementation."""

import base64
import json
import urllib.request
from pathlib import Path
from typing import Union

from agent_tools.vision.base import VisionClient, VisionResult
from agent_tools.utils.config import get_env, load_dotenv


class OllamaVisionClient(VisionClient):
    """Vision client using Ollama Cloud relay.
    
    Supports models like kimi-k2.5:cloud with vision capabilities.
    
    Usage:
        client = OllamaVisionClient.from_env()
        result = client.analyze_image(
            "/path/to/image.jpg",
            "Extract all text",
            model="kimi-k2.5:cloud"
        )
    """
    
    DEFAULT_MODEL = "kimi-k2.5:cloud"
    
    def __init__(self, host: str = "http://127.0.0.1:11434", default_model: str | None = None):
        """Initialize with Ollama host.
        
        Args:
            host: Ollama API base URL (default: http://127.0.0.1:11434)
            default_model: Optional default model to use
        """
        self.host = host.rstrip("/")
        self.default_model = default_model or self.DEFAULT_MODEL
    
    @classmethod
    def from_env(cls) -> "OllamaVisionClient":
        """Create client from OLLAMA_HOST environment variable."""
        load_dotenv()
        host = get_env("OLLAMA_HOST", default="http://127.0.0.1:11434")
        return cls(host=host)
    
    def _encode_image(self, image_path: Union[str, Path]) -> str:
        """Encode image file to base64 data URL."""
        path = Path(image_path)
        with open(path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        ext = path.suffix.lower().replace(".", "").replace("jpg", "jpeg")
        return f"data:image/{ext};base64,{img_b64}"
    
    def analyze_image(
        self,
        image_path: Union[str, Path],
        prompt: str,
        model: str | None = None,
        timeout: int = 180,
    ) -> VisionResult:
        """Analyze an image using Ollama Cloud.
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt/instruction
            model: Ollama model to use (default: kimi-k2.5:cloud)
            timeout: Request timeout in seconds
            
        Returns:
            VisionResult with description and metadata
        """
        model = model or self.default_model
        data_url = self._encode_image(image_path)
        
        # OpenAI-compatible chat completions endpoint
        url = f"{self.host}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                content = data["choices"][0]["message"]["content"]
                
                return VisionResult(
                    description=content,
                    raw_response=data,
                    model=model,
                )
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e.code} - {e.read().decode()}")
        except Exception as e:
            raise RuntimeError(f"Failed to analyze image: {e}")
