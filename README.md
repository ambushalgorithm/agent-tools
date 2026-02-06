# Agent Tools

Reusable utilities for AI agents running on OpenClaw or similar agent frameworks. Designed for portability, composability, and clean configuration.

## Philosophy

- **Environment-driven config** — No hardcoded secrets. Use `.env` files or env vars.
- **Composable modules** — Import only what you need.
- **Framework-agnostic core** — Works with OpenClaw, but doesn't depend on it.
- **Well-documented** — Every module has docstrings and type hints.

## Installation

```bash
git clone https://github.com/crayon-doing-petri/agent-tools.git
cd agent-tools
pip install -e ".[dev]"
```

Or install specific components:

```bash
pip install -e .  # Core only
pip install -e ".[dev]"  # With dev dependencies
```

## Configuration

Create a `.env` file (never commit this):

```bash
# Venice AI (vision fallback)
VENICE_API_KEY=your_key_here

# Ollama Cloud (primary vision)
OLLAMA_HOST=http://127.0.0.1:11434
```

Or set environment variables directly.

## Modules

### `agent_tools.vision`

Vision/image analysis utilities supporting multiple providers.

#### Venice Client

```python
from agent_tools.vision.venice import VeniceVisionClient

client = VeniceVisionClient.from_env()
result = client.analyze_image(
    image_path="/path/to/diagram.png",
    prompt="Describe this architecture diagram",
    model="qwen3-vl-235b-a22b"
)
print(result.description)
```

#### Ollama Cloud Client

```python
from agent_tools.vision.ollama import OllamaVisionClient

client = OllamaVisionClient.from_env()
result = client.analyze_image(
    image_path="/path/to/diagram.png",
    prompt="Extract all text from this image",
    model="kimi-k2.5:cloud"
)
print(result.description)
```

## Development

```bash
# Format code
black src/
ruff check src/

# Type check
mypy src/

# Test
pytest tests/
```

## Project Structure

```
agent-tools/
├── src/agent_tools/       # Main package
│   ├── __init__.py
│   ├── vision/            # Vision/analysis tools
│   │   ├── __init__.py
│   │   ├── venice.py      # Venice AI client
│   │   ├── ollama.py      # Ollama Cloud client
│   │   └── base.py        # Abstract interfaces
│   └── utils/             # Shared utilities
│       ├── __init__.py
│       └── config.py      # Environment/config helpers
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Additional documentation
├── pyproject.toml         # Package configuration
└── README.md
```

## License

MIT — See LICENSE file for details.

## Contributing

1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `black`, `ruff`, and `mypy` pass
5. Submit a PR with clear description

---

Built primarily for OpenClaw workflows, but designed to work anywhere.
