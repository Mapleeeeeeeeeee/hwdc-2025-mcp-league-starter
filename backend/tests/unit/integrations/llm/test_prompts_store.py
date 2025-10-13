"""Unit tests for PromptsConfigStore."""

import json

import pytest
from src.integrations.llm.prompts_config import AgnoPromptsConfig, PromptConfig
from src.integrations.llm.prompts_store import PromptsConfigStore
from src.shared.exceptions.agno import PromptNotFoundError


@pytest.fixture
def sample_prompts_config():
    """Create a sample prompts configuration."""
    return AgnoPromptsConfig(
        prompts=[
            PromptConfig(
                key="default",
                name="Default",
                enabled=True,
                instructions=["instruction 1", "instruction 2"],
            ),
            PromptConfig(
                key="analytical",
                name="Analytical",
                enabled=False,
                instructions=["analyze this", "be detailed"],
            ),
        ],
        system_message="You are a helpful assistant.",
    )


@pytest.fixture
def config_file(tmp_path, sample_prompts_config):
    """Create a temporary config file."""
    config_path = tmp_path / "agno_prompts.json"
    config_path.write_text(json.dumps(sample_prompts_config.model_dump(), indent=2))
    return config_path


def test_load_config__valid_file__returns_config(config_file):
    """Test that _load_config returns parsed configuration."""
    store = PromptsConfigStore(config_path=config_file)
    config = store._load_config()

    assert isinstance(config, AgnoPromptsConfig)
    assert len(config.prompts) == 2
    assert config.prompts[0].key == "default"
    assert config.system_message == "You are a helpful assistant."


def test_load_config__missing_file__returns_default_config_with_two_prompts(tmp_path):
    """Test that missing file loads default configuration with 2 prompts."""
    missing_path = tmp_path / "nonexistent.json"
    store = PromptsConfigStore(config_path=missing_path)
    config = store._load_config()

    assert isinstance(config, AgnoPromptsConfig)
    assert len(config.prompts) == 2  # Default has 2 prompts
    assert config.prompts[0].key == "default"
    assert config.prompts[1].key == "hwdc_demo_prompt"
    assert config.system_message is None


def test_load_config__missing_file__creates_config_file_with_defaults(tmp_path):
    """Test that missing config file gets created with default content."""
    missing_path = tmp_path / "config" / "agno_prompts.json"
    store = PromptsConfigStore(config_path=missing_path)

    # File shouldn't exist initially
    assert not missing_path.exists()

    # Load config (should copy defaults)
    store._load_config()

    # File should now exist
    assert missing_path.exists()

    # Verify the copied content
    with missing_path.open("r", encoding="utf-8") as f:
        copied_data = json.load(f)

    assert len(copied_data["prompts"]) == 2
    assert copied_data["prompts"][0]["key"] == "default"
    assert copied_data["prompts"][1]["key"] == "hwdc_demo_prompt"


def test_get_prompt_by_key__existing_key__returns_prompt(config_file):
    """Test getting a prompt by key returns the correct prompt."""
    store = PromptsConfigStore(config_path=config_file)
    prompt = store.get_prompt_by_key("analytical")

    assert prompt.key == "analytical"
    assert prompt.name == "Analytical"
    assert prompt.enabled is False


def test_get_prompt_by_key__nonexistent_key__raises_error(config_file):
    """Test getting nonexistent prompt raises PromptNotFoundError."""
    store = PromptsConfigStore(config_path=config_file)

    with pytest.raises(PromptNotFoundError) as exc_info:
        store.get_prompt_by_key("nonexistent")

    assert "nonexistent" in str(exc_info.value)


def test_get_instructions__existing_enabled_prompt__returns_instructions(config_file):
    """Test getting instructions from enabled prompt."""
    store = PromptsConfigStore(config_path=config_file)
    instructions = store.get_instructions("default")

    assert isinstance(instructions, list)
    assert len(instructions) == 2
    assert instructions[0] == "instruction 1"


def test_get_instructions__disabled_prompt__raises_error(config_file):
    """Test getting instructions from disabled prompt raises error."""
    store = PromptsConfigStore(config_path=config_file)

    with pytest.raises(PromptNotFoundError) as exc_info:
        store.get_instructions("analytical")

    assert "analytical" in str(exc_info.value)


def test_get_instructions__nonexistent_key__raises_error(config_file):
    """Test getting instructions for nonexistent key raises error."""
    store = PromptsConfigStore(config_path=config_file)

    with pytest.raises(PromptNotFoundError):
        store.get_instructions("nonexistent")


def test_get_system_message__returns_message(config_file):
    """Test getting system message."""
    store = PromptsConfigStore(config_path=config_file)
    message = store.get_system_message()

    assert message == "You are a helpful assistant."


def test_list_available_prompts__returns_all_prompts(config_file):
    """Test listing all available prompts."""
    store = PromptsConfigStore(config_path=config_file)
    prompts = store.list_available_prompts()

    assert len(prompts) == 2
    assert prompts[0]["key"] == "default"
    assert prompts[0]["enabled"] is True
    assert prompts[1]["key"] == "analytical"
    assert prompts[1]["enabled"] is False


def test_update_prompt_enabled__existing_key__saves_to_file(config_file):
    """Test updating prompt enabled state persists to file."""
    store = PromptsConfigStore(config_path=config_file)

    # Enable the analytical prompt
    store.update_prompt_enabled("analytical", True)

    # Reload and verify
    config = store._load_config()
    analytical = next(p for p in config.prompts if p.key == "analytical")
    assert analytical.enabled is True


def test_update_prompt_enabled__nonexistent_key__raises_error(config_file):
    """Test updating nonexistent prompt raises PromptNotFoundError."""
    store = PromptsConfigStore(config_path=config_file)

    with pytest.raises(PromptNotFoundError) as exc_info:
        store.update_prompt_enabled("nonexistent", True)

    assert "nonexistent" in str(exc_info.value)
