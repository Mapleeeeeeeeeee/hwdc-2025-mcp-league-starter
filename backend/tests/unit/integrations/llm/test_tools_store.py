"""Unit tests for Agno tools configuration store."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.integrations.llm.tools_store import ToolsConfigStore
from src.shared.exceptions import ToolkitLoadError, ToolkitNotFoundError


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary config file for testing."""
    config_path = tmp_path / "agno_tools.json"
    config_data = {
        "toolkits": [
            {
                "key": "test_toolkit",
                "toolkit_class": "agno.tools.duckduckgo.DuckDuckGoTools",
                "enabled": True,
                "config": {},
            },
            {
                "key": "disabled_toolkit",
                "toolkit_class": "agno.tools.yfinance.YFinanceTools",
                "enabled": False,
                "config": {},
            },
        ],
        "custom_tools": [],
    }
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path


def test_load_config__valid_file__returns_config(temp_config_file: Path) -> None:
    """Test loading a valid configuration file."""
    store = ToolsConfigStore(config_path=temp_config_file)
    config = store._load_config()

    assert len(config.toolkits) == 2
    assert config.toolkits[0].key == "test_toolkit"
    assert config.toolkits[0].enabled is True


def test_load_config__missing_file__returns_empty_config(tmp_path: Path) -> None:
    """Test loading when config file doesn't exist."""
    config_path = tmp_path / "nonexistent.json"
    store = ToolsConfigStore(config_path=config_path)
    config = store._load_config()

    assert len(config.toolkits) == 0
    assert len(config.custom_tools) == 0


def test_get_enabled_toolkits__returns_only_enabled(temp_config_file: Path) -> None:
    """Test getting only enabled toolkits."""
    store = ToolsConfigStore(config_path=temp_config_file)
    enabled = store.get_enabled_toolkits()

    assert len(enabled) == 1
    assert enabled[0].key == "test_toolkit"
    assert enabled[0].enabled is True


def test_get_toolkit_config__existing_key__returns_config(
    temp_config_file: Path,
) -> None:
    """Test getting configuration for an existing toolkit."""
    store = ToolsConfigStore(config_path=temp_config_file)
    config = store.get_toolkit_config("test_toolkit")

    assert config.key == "test_toolkit"
    assert config.enabled is True


def test_get_toolkit_config__nonexistent_key__raises_error(
    temp_config_file: Path,
) -> None:
    """Test getting configuration for a non-existent toolkit."""
    store = ToolsConfigStore(config_path=temp_config_file)

    with pytest.raises(ToolkitNotFoundError) as exc_info:
        store.get_toolkit_config("nonexistent")

    assert "nonexistent" in str(exc_info.value)


@patch("src.integrations.llm.tools_store.importlib.import_module")
def test_load_toolkit_instances__successful_import__returns_instances(
    mock_import: MagicMock,
    temp_config_file: Path,
) -> None:
    """Test successfully loading toolkit instances."""
    # Mock the module and class
    mock_toolkit_class = MagicMock()
    mock_instance = MagicMock()
    mock_toolkit_class.return_value = mock_instance

    mock_module = MagicMock()
    mock_module.DuckDuckGoTools = mock_toolkit_class
    mock_import.return_value = mock_module

    store = ToolsConfigStore(config_path=temp_config_file)
    instances = store.load_toolkit_instances(strict=False)

    assert len(instances) == 1
    assert instances[0] == mock_instance
    mock_import.assert_called_once_with("agno.tools.duckduckgo")


@patch("src.integrations.llm.tools_store.importlib.import_module")
def test_load_toolkit_instances__import_error__non_strict__returns_partial(
    mock_import: MagicMock,
    temp_config_file: Path,
) -> None:
    """Test loading with import error in non-strict mode."""
    mock_import.side_effect = ImportError("Module not found")

    store = ToolsConfigStore(config_path=temp_config_file)
    instances = store.load_toolkit_instances(strict=False)

    # Should return empty list but not raise
    assert len(instances) == 0


@patch("src.integrations.llm.tools_store.importlib.import_module")
def test_load_toolkit_instances__import_error__strict__raises_error(
    mock_import: MagicMock,
    temp_config_file: Path,
) -> None:
    """Test loading with import error in strict mode."""
    mock_import.side_effect = ImportError("Module not found")

    store = ToolsConfigStore(config_path=temp_config_file)

    with pytest.raises(ToolkitLoadError) as exc_info:
        store.load_toolkit_instances(strict=True)

    assert "test_toolkit" in str(exc_info.value)
    assert "Module not found" in str(exc_info.value)


@patch("src.integrations.llm.tools_store.importlib.import_module")
def test_load_toolkit_instances__attribute_error__strict__raises_error(
    mock_import: MagicMock,
    temp_config_file: Path,
) -> None:
    """Test loading with attribute error in strict mode."""
    mock_module = MagicMock()
    mock_module.DuckDuckGoTools = None  # Simulate missing attribute
    mock_import.return_value = mock_module

    # Make getattr raise AttributeError
    def mock_getattr(obj, name):
        raise AttributeError(f"module has no attribute '{name}'")

    store = ToolsConfigStore(config_path=temp_config_file)

    with patch("builtins.getattr", side_effect=mock_getattr):
        with pytest.raises(ToolkitLoadError) as exc_info:
            store.load_toolkit_instances(strict=True)

        assert "test_toolkit" in str(exc_info.value)


def test_update_toolkit_enabled__saves_to_file(temp_config_file: Path) -> None:
    """Test updating toolkit enabled state."""
    store = ToolsConfigStore(config_path=temp_config_file)

    # Disable the enabled toolkit
    store.update_toolkit_enabled("test_toolkit", False)

    # Reload and verify
    store._config = None  # Clear cache
    config = store._load_config()
    toolkit = next(tk for tk in config.toolkits if tk.key == "test_toolkit")
    assert toolkit.enabled is False

    # Re-enable it
    store.update_toolkit_enabled("test_toolkit", True)

    # Reload and verify again
    store._config = None
    config = store._load_config()
    toolkit = next(tk for tk in config.toolkits if tk.key == "test_toolkit")
    assert toolkit.enabled is True
