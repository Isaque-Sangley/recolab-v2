"""
Entity: User

Representa um usuário no sistema de recomendação.
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional

from ..value_objects import Timestamp, UserId


@dataclass
class User:
    """
    Entidade: Usuário (Aggregate Root)

    Responsabilidades:
    - Manter perfil do usuário
    - Classificar tipo de usuário
    - Calcular métricas de atividade
    - Registrar atividades
    """

    id: UserId
    created_at: Timestamp
    n_ratings: int = 0
    avg_rating: float = 0.0
    last_activity: Optional[Timestamp] = None
    favorite_genres: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validações após inicialização"""
        if self.n_ratings < 0:
            raise ValueError(f"n_ratings cannot be negative: {self.n_ratings}")

        if not (0.0 <= self.avg_rating <= 5.0):
            raise ValueError(f"avg_rating must be 0-5: {self.avg_rating}")

    def mark_activity(self) -> None:
        """
        Marca atividade recente do usuário.

        Atualiza last_activity para agora.
        Chamado toda vez que usuário interage com o sistema.
        """
        self.last_activity = Timestamp.now()

    def classify_type(self) -> str:
        """
        Classifica tipo de usuário baseado em n_ratings.

        Regras de negócio:
        - 0 ratings: cold_start (novo, sem dados)
        - 1-4 ratings: new (recente, poucos dados)
        - 5-19 ratings: casual (uso moderado)
        - 20-99 ratings: active (uso frequente)
        - 100+ ratings: power_user (super engajado)

        Returns:
            String com tipo do usuário
        """
        if self.n_ratings == 0:
            return "cold_start"
        elif self.n_ratings < 5:
            return "new"
        elif self.n_ratings < 20:
            return "casual"
        elif self.n_ratings < 100:
            return "active"
        else:
            return "power_user"

    def calculate_activity_score(self) -> float:
        """
        Score de atividade do usuário (0-1).

        Considera:
        - Número de ratings (logarítmico, para não dominar)
        - Recência de atividade (ativo nos últimos 30 dias)

        Returns:
            Score de 0.0 (inativo) a 1.0 (muito ativo)
        """
        # Componente 1: Número de ratings (escala log)
        # log(100) ≈ 4.6, então usuário com 100 ratings tem score ~1.0
        rating_score = min(1.0, math.log(self.n_ratings + 1) / math.log(100))

        # Componente 2: Recência (ativo nos últimos 30 dias = 1.0)
        recency_score = 1.0 if self.is_active_user() else 0.5

        # Média ponderada (60% quantidade, 40% recência)
        return (0.6 * rating_score) + (0.4 * recency_score)

    def is_active_user(self) -> bool:
        """
        Verifica se usuário está ativo (atividade nos últimos 30 dias).

        Returns:
            True se ativo, False se inativo
        """
        if not self.last_activity:
            return False
        return self.last_activity.age_in_days() <= 30

    def is_new_user(self) -> bool:
        """
        Verifica se é usuário novo (< 5 ratings).

        Returns:
            True se novo, False se experiente
        """
        return self.n_ratings < 5

    def record_rating(self, rating_value: float) -> None:
        """
        Registra uma nova avaliação.

        Atualiza estatísticas do usuário:
        - Incrementa n_ratings
        - Atualiza avg_rating (média incremental)
        - Marca atividade

        Args:
            rating_value: valor do rating (0.5-5.0)
        """
        new_total = (self.avg_rating * self.n_ratings) + rating_value
        self.n_ratings += 1
        self.avg_rating = new_total / self.n_ratings
        self.mark_activity()

    def update_favorite_genres(self, genres: List[str]) -> None:
        """
        Atualiza gêneros favoritos do usuário.

        Args:
            genres: lista de gêneros (máximo 5)

        Raises:
            ValueError: se mais de 5 gêneros
        """
        if len(genres) > 5:
            raise ValueError("Maximum 5 favorite genres allowed")
        self.favorite_genres = genres[:5]

    def get_user_type(self) -> str:
        """Alias para classify_type() (mais intuitivo)"""
        return self.classify_type()

    def get_cf_weight(self) -> float:
        """
        Peso para Collaborative Filtering baseado no tipo de usuário.

        Regra de negócio:
        - Mais ratings = mais confiança em CF
        - Menos ratings = menos confiança em CF

        Returns:
            Peso de 0.0 a 1.0
        """
        weights = {
            "cold_start": 0.1,  # CF quase não funciona
            "new": 0.2,  # CF muito limitado
            "casual": 0.4,  # CF começa a funcionar
            "active": 0.6,  # CF funciona bem
            "power_user": 0.75,  # CF funciona excelente
        }
        return weights.get(self.classify_type(), 0.5)

    def get_cb_weight(self) -> float:
        """
        Peso para Content-Based (complementar ao CF).

        Content-Based funciona melhor com poucos dados,
        então é o inverso do CF.

        Returns:
            Peso de 0.0 a 1.0
        """
        return 1.0 - self.get_cf_weight()

    def __eq__(self, other: object) -> bool:
        """
        Entities são comparadas por ID (identidade).

        Diferente de Value Objects que comparam por valor.
        """
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash baseado no ID (permite usar em sets/dicts)"""
        return hash(self.id)

    def __repr__(self) -> str:
        """Representação string para debugging"""
        return (
            f"User(id={self.id}, type={self.classify_type()}, "
            f"ratings={self.n_ratings}, avg={self.avg_rating:.2f})"
        )
