from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB__", env_file=".env", extra="ignore")

    postgres_url: str = "postgresql+asyncpg://cati:cati@localhost:5432/cati"
    redis_url: str = "redis://localhost:6379/0"
    pool_size: int = 10
    echo_sql: bool = False


class SignalWireSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIGNALWIRE__", env_file=".env", extra="ignore")

    project_id: str = ""
    api_token: str = ""
    space_url: str = ""
    outbound_number: str = ""
    webhook_base_url: str = "http://localhost:8000"


class TTSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TTS__", env_file=".env", extra="ignore")

    provider: Literal["kokoro", "xtts"] = "kokoro"
    kokoro_model: str = "kokoro-v1.0"
    kokoro_voice: str = "af_sky"
    kokoro_device: Literal["cuda", "cpu"] = "cpu"
    xtts_model_path: str = "/models/xtts-v2"
    voice_sample_path: str = ""


class STTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STT__", env_file=".env", extra="ignore")

    provider: Literal["faster_whisper"] = "faster_whisper"
    model_size: str = "large-v3-turbo"
    device: Literal["cuda", "cpu"] = "cpu"
    compute_type: str = "float32"
    language: str = "en"
    vad_enabled: bool = True
    vad_threshold: float = 0.5


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM__", env_file=".env", extra="ignore")

    primary_provider: Literal["anthropic", "openai"] = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.3

    # Cost optimisation: cheaper/faster model for live response parsing.
    # Set to "" to reuse the primary model (safe default).
    # Recommended: "claude-haiku-4-5-20251001" (Anthropic) or "gpt-4o-mini" (OpenAI)
    parsing_model: str = ""
    parsing_max_tokens: int = 256


class ExportSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXPORT__", env_file=".env", extra="ignore")

    export_dir: str = "/data/exports"
    google_service_account_json: str = ""
    google_sheets_folder_id: str = ""


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CELERY__", env_file=".env", extra="ignore")

    broker_url: str = "redis://localhost:6379/1"
    result_backend: str = "redis://localhost:6379/2"
    call_concurrency: int = 5
    worker_concurrency: int = 4


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = False
    api_key: str = Field(default="change-me", alias="API_KEY")

    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    signalwire: SignalWireSettings = Field(default_factory=SignalWireSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    stt: STTSettings = Field(default_factory=STTSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
