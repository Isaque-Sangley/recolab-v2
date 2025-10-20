"""
Application Configuration

Configurações centralizadas da aplicação.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Configurações da aplicação.
    
    Carrega de variáveis de ambiente ou .env file.
    """
    
    # App
    app_name: str = "RecoLab API"
    app_version: str = "2.0.0"
    app_description: str = "Sistema de Recomendação de Filmes com Deep Learning"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql+asyncpg://recolab:recolab123@localhost:5432/recolab"
    sql_echo: bool = False
    
    # CORS
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # ML
    models_path: str = "models"
    cache_ttl: int = 3600  # 1 hora
    
    # API
    api_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retorna configurações (singleton)"""
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    return _settings