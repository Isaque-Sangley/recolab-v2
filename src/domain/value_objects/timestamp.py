"""
Value Object: Timestamp

Representa um momento no tempo.
Encapsula datetime e adiciona métodos úteis.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Timestamp:
    """
    Momento no tempo.
    
    Por que não usar datetime direto?
    - Adiciona métodos de domínio (is_recent, age_in_days)
    - Garante timezone awareness
    - Consistência em toda aplicação
    """
    
    value: datetime
    
    def __post_init__(self):
        if not isinstance(self.value, datetime):
            raise ValueError(f"Timestamp must be datetime, got {type(self.value)}")
    
    @classmethod
    def now(cls) -> 'Timestamp':
        """Cria timestamp com momento atual"""
        return cls(value=datetime.now())
    
    @classmethod
    def from_iso(cls, iso_string: str) -> 'Timestamp':
        """Cria timestamp a partir de string ISO"""
        return cls(value=datetime.fromisoformat(iso_string))
    
    def to_iso(self) -> str:
        """Converte para string ISO"""
        return self.value.isoformat()
    
    def __str__(self) -> str:
        return self.value.strftime("%Y-%m-%d %H:%M:%S")
    
    def is_recent(self, days: int = 7) -> bool:
        """Verifica se timestamp é recente (últimos N dias)"""
        age = datetime.now() - self.value
        return age.days <= days
    
    def age_in_days(self) -> int:
        """Retorna idade em dias"""
        age = datetime.now() - self.value
        return age.days
    
    def __lt__(self, other: 'Timestamp') -> bool:
        return self.value < other.value
    
    def __le__(self, other: 'Timestamp') -> bool:
        return self.value <= other.value
    
    def __gt__(self, other: 'Timestamp') -> bool:
        return self.value > other.value
    
    def __ge__(self, other: 'Timestamp') -> bool:
        return self.value >= other.value