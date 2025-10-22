"""
Value Object: RatingScore

Representa a pontuação de uma avaliação (0.5-5.0 estrelas).
Garante que ratings são sempre válidos.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RatingScore:
    """
    Pontuação de avaliação (escala 0.5-5.0, incrementos de 0.5).

    MovieLens usa escala: 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0

    Por que não usar float direto?
    - Validação: garante range 0.5-5.0 e incrementos corretos
    - Semântica: auto-documentado
    - Evolução: fácil mudar lógica depois
    """

    value: float

    MIN_SCORE: float = 0.5
    MAX_SCORE: float = 5.0

    def __post_init__(self):
        """Validação na criação"""
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"RatingScore must be numeric, got {type(self.value)}")

        # Validação de range
        if not (self.MIN_SCORE <= self.value <= self.MAX_SCORE):
            raise ValueError(
                f"RatingScore must be between {self.MIN_SCORE} and {self.MAX_SCORE}, "
                f"got {self.value}"
            )

        # Validação de incrementos (deve ser múltiplo de 0.5)
        # Multiplica por 2 e verifica se é inteiro
        if (self.value * 2) % 1 != 0:
            raise ValueError(
                f"RatingScore must be in 0.5 increments (0.5, 1.0, 1.5, ..., 5.0), "
                f"got {self.value}"
            )

    def __float__(self) -> float:
        return float(self.value)

    def __str__(self) -> str:
        return f"{self.value:.1f}★"

    def is_positive(self) -> bool:
        """Rating é considerado positivo se >= 4.0"""
        return self.value >= 4.0

    def is_negative(self) -> bool:
        """Rating é considerado negativo se <= 2.5"""
        return self.value <= 2.5

    def normalize(self) -> float:
        """
        Normaliza para range 0-1 (útil para ML).

        Mapeia [0.5, 5.0] → [0, 1]
        """
        return (self.value - self.MIN_SCORE) / (self.MAX_SCORE - self.MIN_SCORE)
