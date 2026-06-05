"""
Settings management for digital-fasting-companion.

Uses pydantic-settings for environment-based configuration.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    db_path: str = Field(
        default="app.db",
        description="Database filename (relative to data_dir)"
    )
    db_key: str = Field(
        default="",
        description="Encryption key for SQLCipher (256-bit)"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        extra="ignore"
    )


class InterventionSettings(BaseSettings):
    """Intervention threshold settings."""
    
    # Tier thresholds
    tier1_min_score: float = Field(default=0.4, ge=0.0, le=1.0)
    tier1_max_score: float = Field(default=0.6, ge=0.0, le=1.0)
    tier2_min_score: float = Field(default=0.6, ge=0.0, le=1.0)
    tier2_max_score: float = Field(default=0.8, ge=0.0, le=1.0)
    tier3_min_score: float = Field(default=0.8, ge=0.0, le=1.0)
    tier3_max_score: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Time thresholds (minutes)
    session_threshold_ai: int = Field(default=120, ge=1)
    session_threshold_social: int = Field(default=180, ge=1)
    
    # Cooldown periods (minutes)
    tier_cooldown_minutes: int = Field(default=15, ge=1)
    inter_tier_cooldown_minutes: int = Field(default=5, ge=1)
    
    model_config = SettingsConfigDict(
        env_prefix="TIER_",
        extra="ignore"
    )


class FatigueDetectionSettings(BaseSettings):
    """Fatigue detection ML model settings."""
    
    feature_window_seconds: int = Field(default=300, ge=60)
    prediction_interval_seconds: int = Field(default=60, ge=10)
    online_learning_weeks: int = Field(default=1, ge=1)
    
    # Model hyperparameters
    n_estimators: int = Field(default=100, ge=10)
    max_depth: int = Field(default=8, ge=1)
    min_samples_split: int = Field(default=2, ge=2)
    
    model_config = SettingsConfigDict(
        env_prefix="ML_",
        extra="ignore"
    )


class OllamaSettings(BaseSettings):
    """Ollama local LLM settings."""
    
    host: str = Field(default="http://localhost:11434")
    model: str = Field(default="tinyllama")
    timeout_seconds: int = Field(default=30, ge=5)
    
    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_",
        extra="ignore"
    )


class MonitoringSettings(BaseSettings):
    """Monitoring settings."""
    
    keystroke_sample_interval_ms: int = Field(default=100, ge=50)
    screen_time_poll_interval_seconds: int = Field(default=30, ge=5)
    
    model_config = SettingsConfigDict(
        env_prefix="MONITOR_",
        extra="ignore"
    )


class Settings(BaseSettings):
    """
    Main application settings.
    
    Loads from environment variables with .env file support.
    """
    
    # App info
    app_name: str = Field(default="digital-fasting-companion")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Paths
    data_dir: Path = Field(default=Path("./data"))
    config_dir: Path = Field(default=Path("./config"))
    log_dir: Path = Field(default=Path("./logs"))
    
    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    intervention: InterventionSettings = Field(default_factory=InterventionSettings)
    fatigue_detection: FatigueDetectionSettings = Field(default_factory=FatigueDetectionSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    # API keys (loaded from environment)
    claude_api_key: Optional[str] = Field(default=None, exclude_from_schema=True)
    openai_api_key: Optional[str] = Field(default=None, exclude_from_schema=True)
    garmin_password: Optional[str] = Field(default=None, exclude_from_schema=True)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def db_path_full(self) -> Path:
        """Full database path."""
        return self.data_dir / self.database.db_path
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key from keyring or environment."""
        if provider == "claude":
            return self.claude_api_key
        elif provider == "openai":
            return self.openai_api_key
        elif provider == "garmin":
            return self.garmin_password
        return None
    
    def is_llm_available(self, provider: str) -> bool:
        """Check if LLM provider is available."""
        if provider == "ollama":
            return True  # Always available if running
        elif provider == "claude":
            return bool(self.claude_api_key)
        elif provider == "openai":
            return bool(self.openai_api_key)
        return False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
