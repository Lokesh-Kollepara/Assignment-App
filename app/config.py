"""
Configuration settings for the PDF Hint Chatbot application.
"""
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    GEMINI_API_KEY: str

    # Application Configuration
    APP_NAME: str = "PDF Hint Chatbot"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    PDF_MATERIALS_DIR: Path = DATA_DIR / "pdfs" / "materials"
    PDF_ASSIGNMENTS_DIR: Path = DATA_DIR / "pdfs" / "assignments"
    STATIC_DIR: Path = BASE_DIR / "static"

    # Chat Configuration
    MAX_HISTORY_LENGTH: int = 20
    SESSION_TIMEOUT_MINUTES: int = 60

    # LLM Configuration
    MODEL_NAME: str = "gemini-2.0-flash-exp"
    TEMPERATURE: float = 0.7
    MAX_OUTPUT_TOKENS: int = 1024
    TOP_P: float = 0.9
    TOP_K: int = 40

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
