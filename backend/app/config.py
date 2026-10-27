import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json

class Settings(BaseSettings):
    APP_NAME: str = "DataLens"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # Database
    DATABASE_URL: str = "sqlite:///./datalens.db"
    
    # Storage
    STORAGE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
