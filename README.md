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

### Environment Check

```bash
# Check what's configured
python -m agent_tools check

# or after pip install:
agent-tools check
```

### Tool Discovery

```python
from agent_tools import list_tools, get_tool, discover

# List all tools
for tool in list_tools():
    print(f"{tool.name}: {tool.description}")

# Only show configured/ready tools
for tool in list_tools(only_available=True):
    print(f"✅ {tool.name} is ready")

# Get discovery info as dict
info = discover()
print(f"{info['available']}/{info['total']} tools ready")

# Get a tool class dynamically
OllamaVisionClient = get_tool("vision.ollama")
client = OllamaVisionClient.from_env()
```

### CLI Usage

```bash
# Human-readable list
agent-tools list

# Machine-readable JSON
agent-tools json

# Check environment
agent-tools check
```

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
│   ├── cli.py            # CLI for tool discovery
│   ├── registry.py       # Auto-discovery registry
│   ├── vision/            # Vision/analysis tools
│   │   ├── __init__.py
│   │   ├── base.py        # Abstract interfaces
│   │   ├── ollama.py      # Ollama Cloud client
│   │   └── venice.py      # Venice AI client
│   └── utils/             # Shared utilities
│       ├── __init__.py
│       └── config.py      # Environment/config helpers
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Additional documentation
├── pyproject.toml         # Package configuration
└── README.md
```

## Auto-Discovery

The package supports runtime tool discovery — useful for agents that need to:

1. **Introspect** what's available without hardcoding imports
2. **Check configuration** before attempting to use a tool
3. **Dynamically select** the best available tool for a task

### Programmatic Discovery

```python
from agent_tools import list_tools, get_tool, discover

# List all tools
for tool in list_tools():
    print(f"{tool.name}: {tool.description}")

# Check what's configured
for tool in list_tools(only_available=True):
    print(f"✅ {tool.name} ready")

# Get full discovery dict
info = discover()
print(f"{info['available']}/{info['total']} tools configured")
```

### CLI Discovery

```bash
# After pip install:
agent-tools list      # Human-readable
agent-tools json      # Machine-readable
agent-tools check     # Environment verification
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
