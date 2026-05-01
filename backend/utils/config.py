"""Configuration & Settings"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS: int = 8192
    MAX_CONCURRENT_ANALYSES: int = 5
    ANALYSIS_TIMEOUT_SECONDS: int = 300
    UPLOAD_DIR: str = "/tmp/paper_uploads"
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
