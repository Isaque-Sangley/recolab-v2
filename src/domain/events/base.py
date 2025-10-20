"""
Base Domain Event

Classe base para todos os eventos de domínio.
"""

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class para eventos de domínio.
    
    Todos os eventos herdam desta classe.
    Eventos são imutáveis (frozen=True).
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = "domain.event"