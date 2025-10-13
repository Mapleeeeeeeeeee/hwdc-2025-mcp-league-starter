"""Unit tests for the LLM model configuration store."""

from __future__ import annotations

import json

import pytest
from src.core.exceptions import NotFoundError
from src.integrations.llm import LLMModelConfig, ModelConfigStore


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset ModelConfigStore singleton between tests."""
    yield
    # Reset singleton state after each test
    ModelConfigStore._instance = None
    ModelConfigStore._class_initialized = False


def _make_store(tmp_path) -> ModelConfigStore:
    models_path = tmp_path / "models.json"
    active_path = tmp_path / "active.json"
    return ModelConfigStore(models_path=models_path, active_path=active_path)


def test_list_configs__initializes_defaults(tmp_path) -> None:
    store = _make_store(tmp_path)

    configs = store.list_configs()

    assert configs, "expected default model configurations to be created"


def test_get_config__unknown_key__raises_not_found_error(tmp_path) -> None:
    store = _make_store(tmp_path)

    with pytest.raises(NotFoundError):
        store.get_config("does-not-exist")


def test_set_active_model_key__unknown_key__raises_not_found_error(tmp_path) -> None:
    store = _make_store(tmp_path)

    with pytest.raises(NotFoundError):
        store.set_active_model_key("missing-key")


def test_upsert_config__persists_to_disk(tmp_path) -> None:
    store = _make_store(tmp_path)
    new_config = LLMModelConfig(
        key="custom:model",
        provider="openai",
        model_id="gpt-5-custom",
        metadata={},
    )

    store.upsert_config(new_config)

    reloaded = _make_store(tmp_path)
    keys = {cfg.key for cfg in reloaded.list_configs()}

    assert "custom:model" in keys


def test_get_active_model_key__empty_file__falls_back_to_default(tmp_path) -> None:
    store = _make_store(tmp_path)
    expected_default = store.get_active_model_key()

    store._active_path.write_text("", encoding="utf-8")

    assert store.get_active_model_key() == expected_default


def test_get_active_model_key__invalid_json__raises_value_error(tmp_path) -> None:
    store = _make_store(tmp_path)
    store._active_path.write_text(json.dumps({"wrong": "format"}), encoding="utf-8")

    with pytest.raises(ValueError):
        store.get_active_model_key()
