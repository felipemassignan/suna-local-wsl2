"""
Configuration management for SUNA Local
Adaptado para funcionar totalmente local no WSL2
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseSettings


class EnvMode(str, Enum):
    LOCAL = "LOCAL"
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class Config(BaseSettings):
    """Configuration settings for SUNA Local"""
    
    # Environment mode
    ENV_MODE: EnvMode = EnvMode.LOCAL
    
    # API Keys (optional in LOCAL mode)
    OPENAI_API_KEY: Optional[str] = "sk-dummy-key"
    OPENAI_API_BASE: Optional[str] = "http://localhost:8000/v1"
    TAVILY_API_KEY: Optional[str] = None
    
    # Database settings (optional in LOCAL mode)
    SUPABASE_URL: Optional[str] = "https://dummy.supabase.co"
    SUPABASE_KEY: Optional[str] = "dummy-key"
    
    # Local database settings
    SQLITE_DB_PATH: str = "./data/sqlite/suna.db"
    VECTOR_STORE_PATH: str = "./data/vector_store"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Local paths
    MODELS_PATH: str = "./models"
    DATA_PATH: str = "./data"
    LOGS_PATH: str = "./data/logs"
    
    # Server settings
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8080
    LLAMA_HOST: str = "0.0.0.0"
    LLAMA_PORT: int = 8000
    
    # Model settings
    DEFAULT_MODEL: str = "local-mistral"
    MODEL_FILE: str = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # Local mode settings
    LOCAL_USER_ID: str = "local-user-123"
    LOCAL_PROJECT_ID: str = "local-project-123"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global config instance
config = Config()


def is_local_mode() -> bool:
    """Check if running in local mode"""
    return config.ENV_MODE == EnvMode.LOCAL


def get_model_path() -> str:
    """Get full path to the model file"""
    return os.path.join(config.MODELS_PATH, config.MODEL_FILE)


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        config.DATA_PATH,
        config.LOGS_PATH,
        config.MODELS_PATH,
        config.VECTOR_STORE_PATH,
        os.path.dirname(config.SQLITE_DB_PATH)
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

