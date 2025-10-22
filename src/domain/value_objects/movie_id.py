"""
Value Object: MovieId

Identidade única de um filme/item.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class MovieId:
    """
    Representa a identidade única de um filme.

    Separado de UserId para type safety:
    - Impossível passar MovieId onde espera UserId
    - Compilador/IDE ajuda a evitar bugs
    """

    value: int

    def __post_init__(self):
        # Aceita int nativo E numpy integers
        if not isinstance(self.value, (int, np.integer)):
            raise ValueError(f"MovieId must be an integer, got {type(self.value)}")

        # Converte numpy int para Python int
        if isinstance(self.value, np.integer):
            object.__setattr__(self, "value", int(self.value))

        if self.value <= 0:
            raise ValueError(f"MovieId must be positive, got {self.value}")

    def __str__(self) -> str:
        return f"Movie#{self.value}"

    def __int__(self) -> int:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MovieId):
            return False
        return self.value == other.value
