"""
Database Package

Configuração e modelos do banco de dados.
"""

from .config import DatabaseConfig, get_database_config, get_session
from .models import (
    Base,
    ModelMetadataModel,
    MovieModel,
    RatingModel,
    RecommendationModel,
    UserModel,
)

__all__ = [
    "DatabaseConfig",
    "get_database_config",
    "get_session",
    "Base",
    "UserModel",
    "MovieModel",
    "RatingModel",
    "RecommendationModel",
    "ModelMetadataModel",
]
