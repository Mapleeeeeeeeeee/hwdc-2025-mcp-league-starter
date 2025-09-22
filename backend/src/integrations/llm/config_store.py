"""Persistent store for LLM model configurations."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from threading import Lock
from typing import Any

from src.config import settings
from src.core.exceptions import NotFoundError

from .model_config import LLMModelConfig, LLMModelRegistryFile

_DEFAULT_MODELS: list[dict[str, Any]] = [
    {
        "key": "openai:gpt-4o-mini",
        "provider": "openai",
        "model_id": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "supports_streaming": True,
        "default_params": {"temperature": 0.7},
        "metadata": {"display_name": "OpenAI GPT-4o mini"},
    },
    {
        "key": "ollama:llama3.1",
        "provider": "ollama",
        "model_id": "llama3.1",
        "supports_streaming": True,
        "metadata": {"display_name": "Ollama Llama 3.1"},
    },
]
_DEFAULT_ACTIVE_KEY: str = str(_DEFAULT_MODELS[0]["key"])


class ModelConfigStore:
    """Loads and persists model configuration without hardcoding providers."""

    def __init__(
        self,
        models_path: Path | None = None,
        active_path: Path | None = None,
    ) -> None:
        self._models_path = models_path or settings.llm_models_file
        self._active_path = active_path or settings.llm_active_model_file
        self._lock = Lock()
        self._ensure_files()

    def list_configs(self) -> list[LLMModelConfig]:
        raw_models = self._read_models_file()
        configs: list[LLMModelConfig] = []
        for item in raw_models:
            configs.append(LLMModelConfig(**item))
        return configs

    def get_config(self, key: str) -> LLMModelConfig:
        for config in self.list_configs():
            if config.key == key:
                return config
        msg = f"Model configuration '{key}' not found"
        raise NotFoundError(
            detail=msg,
            i18n_key="errors.model_config.not_found",
            i18n_params={"key": key},
        )

    def get_active_model_key(self) -> str:
        with self._lock:
            if not self._active_path.exists():
                self._write_active_key(_DEFAULT_ACTIVE_KEY)
                return _DEFAULT_ACTIVE_KEY
            raw = self._active_path.read_text(encoding="utf-8").strip()
        return raw or _DEFAULT_ACTIVE_KEY

    def set_active_model_key(self, key: str) -> None:
        # 先驗證是否存在
        _ = self.get_config(key)
        self._write_active_key(key)

    def upsert_configs(self, configs: Iterable[LLMModelConfig]) -> None:
        self._write_configs(configs)

    def upsert_config(self, config: LLMModelConfig) -> None:
        existing = {item.key: item for item in self.list_configs()}
        existing[config.key] = config
        self._write_configs(existing.values())

    def _read_models_file(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self._models_path.exists():
                self._write_default_models()
                return list(_DEFAULT_MODELS)
            raw = self._models_path.read_text(encoding="utf-8")
        if raw.strip() == "":
            return list(_DEFAULT_MODELS)
        data = json.loads(raw)
        if isinstance(data, dict) and "models" in data:
            models = data["models"]
        elif isinstance(data, list):
            models = data
        else:
            msg = "Invalid model configuration file format"
            raise ValueError(msg)
        if not isinstance(models, list):
            raise ValueError("Model configuration file must contain a list of models")
        return [dict(item) for item in models]

    def _ensure_files(self) -> None:
        with self._lock:
            self._models_path.parent.mkdir(parents=True, exist_ok=True)
            if not self._models_path.exists():
                self._write_default_models()
            if not self._active_path.exists():
                self._write_active_key(_DEFAULT_ACTIVE_KEY)

    def _write_default_models(self) -> None:
        registry = LLMModelRegistryFile(
            models=[LLMModelConfig(**cfg) for cfg in _DEFAULT_MODELS]
        )
        serialized = registry.model_dump_json(indent=2)
        self._models_path.write_text(serialized, encoding="utf-8")

    def _write_active_key(self, key: str) -> None:
        with self._lock:
            self._active_path.parent.mkdir(parents=True, exist_ok=True)
            self._active_path.write_text(key, encoding="utf-8")

    def _write_configs(self, configs: Iterable[LLMModelConfig]) -> None:
        payload = LLMModelRegistryFile(models=list(configs))
        with self._lock:
            self._models_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = payload.model_dump_json(indent=2)
            self._models_path.write_text(serialized, encoding="utf-8")


__all__ = ["ModelConfigStore"]
