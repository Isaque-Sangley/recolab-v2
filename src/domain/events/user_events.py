"""
User Domain Events
"""

from dataclasses import dataclass, field
from typing import List
from .base import DomainEvent


@dataclass(frozen=True)
class UserCreated(DomainEvent):
    """Evento: Usuário criado"""
    user_id: int = 0
    event_type: str = "user.created"


@dataclass(frozen=True)
class UserProfileUpdated(DomainEvent):
    """Evento: Perfil do usuário atualizado"""
    user_id: int = 0
    updated_fields: List[str] = field(default_factory=list)
    event_type: str = "user.profile_updated"


@dataclass(frozen=True)
class UserBecameActive(DomainEvent):
    """Evento: Usuário se tornou ativo"""
    user_id: int = 0
    n_ratings: int = 0
    event_type: str = "user.became_active"


@dataclass(frozen=True)
class UserBecamePowerUser(DomainEvent):
    """Evento: Usuário se tornou power user"""
    user_id: int = 0
    n_ratings: int = 0
    event_type: str = "user.became_power_user"