"""Tests for vision base classes."""

import pytest
from pathlib import Path

from agent_tools.vision.base import VisionResult


def test_vision_result_str():
    """Test VisionResult string representation."""
    result = VisionResult(description="test description")
    assert str(result) == "test description"


def test_vision_result_with_metadata():
    """Test VisionResult with all fields."""
    result = VisionResult(
        description="found bots: Patti, Jason",
        model="test-model",
        raw_response={"choices": []}
    )
    assert result.description == "found bots: Patti, Jason"
    assert result.model == "test-model"
    assert result.raw_response == {"choices": []}


def test_import_vision_clients():
    """Test that all vision clients can be imported."""
    from agent_tools.vision import VisionClient, VisionResult
    from agent_tools.vision import VeniceVisionClient, OllamaVisionClient
    
    assert VisionClient is not None
    assert VisionResult is not None
    assert VeniceVisionClient is not None
    assert OllamaVisionClient is not None
