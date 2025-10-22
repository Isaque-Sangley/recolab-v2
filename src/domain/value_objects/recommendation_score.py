"""
Value Object: RecommendationScore

Score de uma recomendação (0-1, quanto maior melhor).
Diferente de RatingScore - tem semântica diferente.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecommendationScore:
    """
    Score de confiança de uma recomendação.

    Range: 0.0 (péssimo) a 1.0 (MUITO BOM)

    Diferente de RatingScore:
    - RatingScore: opinião do usuário (1-5)
    - RecommendationScore: confiança do modelo (0-1)
    """

    value: float

    MIN_SCORE: float = 0.0
    MAX_SCORE: float = 1.0

    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"RecommendationScore must be numeric, got {type(self.value)}")

        if not (self.MIN_SCORE <= self.value <= self.MAX_SCORE):
            raise ValueError(
                f"RecommendationScore must be between {self.MIN_SCORE} and {self.MAX_SCORE}, "
                f"got {self.value}"
            )

    def __float__(self) -> float:
        return float(self.value)

    def __str__(self) -> str:
        percentage = self.value * 100
        return f"{percentage:.1f}%"

    def __lt__(self, other: "RecommendationScore") -> bool:
        """Permite ordenação: sorted(scores)"""
        return self.value < other.value

    def __le__(self, other: "RecommendationScore") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "RecommendationScore") -> bool:
        return self.value > other.value

    def __ge__(self, other: "RecommendationScore") -> bool:
        return self.value >= other.value

    def confidence_level(self) -> str:
        """Retorna nível de confiança humanizado"""
        if self.value >= 0.8:
            return "very_high"
        elif self.value >= 0.6:
            return "high"
        elif self.value >= 0.4:
            return "medium"
        elif self.value >= 0.2:
            return "low"
        else:
            return "very_low"
