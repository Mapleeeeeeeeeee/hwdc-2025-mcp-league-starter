"""Persistent store for LLM model configurations."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from threading import Lock

from pydantic import ValidationError

from src.config import settings
from src.core.exceptions import NotFoundError

from .model_config import LLMModelConfig, LLMModelRegistryFile

_DEFAULT_MODEL_CONFIGS: tuple[LLMModelConfig, ...] = (
    LLMModelConfig(
        key="openai:gpt-5-mini",
        provider="openai",
        model_id="gpt-5-mini",
        api_key_env="OPENAI_API_KEY",
        supports_streaming=True,
        default_params={"temperature": 0.7},
        metadata={"display_name": "OpenAI GPT-5 mini"},
    ),
    LLMModelConfig(
        key="ollama:llama3.1",
        provider="ollama",
        model_id="llama3.1",
        supports_streaming=True,
        metadata={"display_name": "Ollama Llama 3.1"},
    ),
)
_DEFAULT_ACTIVE_KEY: str = _DEFAULT_MODEL_CONFIGS[0].key


class ModelConfigStore:
    """Loads and persists model configuration without hardcoding providers."""

    _instance: ModelConfigStore | None = None
    _class_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        models_path: Path | None = None,
        active_path: Path | None = None,
    ) -> None:
        if ModelConfigStore._class_initialized:
            return

        self._models_path = models_path or settings.llm_models_file
        self._active_path = active_path or settings.llm_active_model_file
        self._lock = Lock()
        self._ensure_files()
        ModelConfigStore._class_initialized = True

    def list_configs(self) -> list[LLMModelConfig]:
        return [config.model_copy(deep=True) for config in self._read_models_file()]

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
        if not raw:
            return _DEFAULT_ACTIVE_KEY
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            msg = "Invalid active model file format"
            raise ValueError(msg) from exc
        if isinstance(data, dict) and "active_model_key" in data:
            value = data["active_model_key"]
            if isinstance(value, str) and value:
                return value
        raise ValueError("Active model file must contain 'active_model_key'")

    def set_active_model_key(self, key: str) -> None:
        # 先驗證是否存在
        _ = self.get_config(key)
        self._write_active_key_with_lock(key)

    def upsert_configs(self, configs: Iterable[LLMModelConfig]) -> None:
        self._write_configs(configs)

    def upsert_config(self, config: LLMModelConfig) -> None:
        existing = {item.key: item for item in self.list_configs()}
        existing[config.key] = config
        self._write_configs(existing.values())

    def _read_models_file(self) -> list[LLMModelConfig]:
        with self._lock:
            if not self._models_path.exists():
                self._write_default_models()
            raw = self._models_path.read_text(encoding="utf-8")
        if raw.strip() == "":
            raise ValueError("Model configuration file cannot be empty")
        try:
            registry = LLMModelRegistryFile.model_validate_json(raw)
        except ValidationError as exc:
            raise ValueError("Invalid model configuration file format") from exc
        return [model.model_copy(deep=True) for model in registry.models]

    def _ensure_files(self) -> None:
        with self._lock:
            self._models_path.parent.mkdir(parents=True, exist_ok=True)
            if not self._models_path.exists():
                self._write_default_models()
            if not self._active_path.exists():
                self._write_active_key(_DEFAULT_ACTIVE_KEY)

    def _write_default_models(self) -> None:
        registry = LLMModelRegistryFile(
            models=[cfg.model_copy(deep=True) for cfg in _DEFAULT_MODEL_CONFIGS]
        )
        serialized = registry.model_dump_json(indent=2)
        self._models_path.write_text(serialized, encoding="utf-8")

    def _write_active_key(self, key: str) -> None:
        self._active_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"active_model_key": key}, indent=2)
        self._active_path.write_text(payload, encoding="utf-8")

    def _write_active_key_with_lock(self, key: str) -> None:
        with self._lock:
            self._write_active_key(key)

    def _write_configs(self, configs: Iterable[LLMModelConfig]) -> None:
        payload = LLMModelRegistryFile(
            models=[cfg.model_copy(deep=True) for cfg in configs]
        )
        with self._lock:
            self._models_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = payload.model_dump_json(indent=2)
            self._models_path.write_text(serialized, encoding="utf-8")
