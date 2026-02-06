"""Venice AI vision client implementation."""

import base64
from pathlib import Path
from typing import Union

from venice_ai import VeniceClient

from agent_tools.vision.base import VisionClient, VisionResult
from agent_tools.utils.config import get_env, load_dotenv


class VeniceVisionClient(VisionClient):
    """Vision client using Venice AI's API.
    
    Supports models like qwen3-vl-235b-a22b for image analysis.
    
    Usage:
        client = VeniceVisionClient.from_env()
        result = client.analyze_image(
            "/path/to/image.jpg",
            "Describe this diagram"
        )
    """
    
    DEFAULT_MODEL = "qwen3-vl-235b-a22b"
    
    def __init__(self, api_key: str, default_model: str | None = None):
        """Initialize with API key.
        
        Args:
            api_key: Venice API key
            default_model: Optional default model to use
        """
        self.client = VeniceClient(api_key=api_key)
        self.default_model = default_model or self.DEFAULT_MODEL
    
    @classmethod
    def from_env(cls) -> "VeniceVisionClient":
        """Create client from VENICE_API_KEY environment variable."""
        load_dotenv()
        api_key = get_env("VENICE_API_KEY", required=True)
        return cls(api_key=api_key)
    
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
        max_tokens: int | None = None,
    ) -> VisionResult:
        """Analyze an image using Venice AI.
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt/instruction
            model: Venice model to use (default: qwen3-vl-235b-a22b)
            max_tokens: Maximum tokens in response
            
        Returns:
            VisionResult with description and metadata
        """
        model = model or self.default_model
        data_url = self._encode_image(image_path)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]
        
        kwargs = {}
        if max_tokens:
            kwargs["max_completion_tokens"] = max_tokens
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )
        
        content = response.choices[0].message.content
        
        return VisionResult(
            description=content,
            raw_response=response.model_dump(),
            model=model,
        )
