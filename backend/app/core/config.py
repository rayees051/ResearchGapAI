import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Adaptive Research Gap AI"
    API_V1_STR: str = "/api/v1"

    # JWT Security Settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Databases & Caching
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Provider Configuration
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None

    # File Storage
    UPLOAD_DIR: str = "storage/papers"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

# Startup logging for Gemini API configuration
# Do NOT print the actual key.
_gemini_key_present = "YES" if settings.GEMINI_API_KEY else "NO"
print(f"Gemini configured: {_gemini_key_present}")

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)