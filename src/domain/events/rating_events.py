"""
Rating Domain Events
"""

from dataclasses import dataclass

from .base import DomainEvent


@dataclass(frozen=True)
class RatingCreated(DomainEvent):
    """Evento: Rating criado"""

    user_id: int = 0
    movie_id: int = 0
    rating: float = 0.0
    event_type: str = "rating.created"


@dataclass(frozen=True)
class RatingUpdated(DomainEvent):
    """Evento: Rating atualizado"""

    user_id: int = 0
    movie_id: int = 0
    old_rating: float = 0.0
    new_rating: float = 0.0
    event_type: str = "rating.updated"


@dataclass(frozen=True)
class RatingDeleted(DomainEvent):
    """Evento: Rating deletado"""

    user_id: int = 0
    movie_id: int = 0
    rating: float = 0.0
    event_type: str = "rating.deleted"
