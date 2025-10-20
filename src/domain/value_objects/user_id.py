"""
Value Object: UserId

Encapsula a identidade de um usuário.
"""

from dataclasses import dataclass
from typing import Any
import numpy as np


@dataclass(frozen=True)
class UserId:
    """
    Representa a identidade única de um usuário.
    
    Por que Value Object?
    - Encapsula validação (não aceita IDs inválidos)
    - Imutável (thread-safe)
    - Comparável por valor (não por referência)
    - Auto-documentado (UserId ao invés de int)
    """
    
    value: int
    
    def __post_init__(self):
        """Valida o ID após inicialização"""
        # Aceita int nativo E numpy integers
        if not isinstance(self.value, (int, np.integer)):
            raise ValueError(f"UserId must be an integer, got {type(self.value)}")
        
        # Converte numpy int para Python int
        if isinstance(self.value, np.integer):
            object.__setattr__(self, 'value', int(self.value))
        
        if self.value <= 0:
            raise ValueError(f"UserId must be positive, got {self.value}")
    
    def __str__(self) -> str:
        return f"User#{self.value}"
    
    def __int__(self) -> int:
        """Permite converter de volta para int quando necessário"""
        return self.value
    
    def __hash__(self) -> int:
        """Permite usar como chave em dicts/sets"""
        return hash(self.value)
    
    def __eq__(self, other: Any) -> bool:
        """Comparação por valor"""
        if not isinstance(other, UserId):
            return False
        return self.value == other.value