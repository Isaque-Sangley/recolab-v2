"""
User Profile Service

Calcula perfil detalhado do usuário baseado em seu histórico.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List

from ..entities import Rating, User
from ..value_objects import UserId


@dataclass
class UserProfile:
    """
    Perfil completo de um usuário.

    Agrega informações de múltiplas fontes.
    """

    user: User
    favorite_genres: List[str]
    genre_affinity: Dict[str, float]  # gênero → score (0-1)
    rating_distribution: Dict[int, int]  # rating → count
    avg_rating: float
    rating_variance: float
    is_generous_rater: bool  # Dá notas altas
    is_critical_rater: bool  # Dá notas baixas
    activity_score: float  # 0-1
    diversity_score: float  # 0-1, diversidade de gêneros
    engagement_level: str  # "low", "medium", "high"


class UserProfileService:
    """
    Domain Service: Cálculo de Perfil de Usuário

    Por que é Domain Service?
    - Lógica de negócio complexa
    - Coordena múltiplas entities (User + Ratings)
    - Não pertence a nenhuma Entity específica

    Responsabilidades:
    - Calcular perfil detalhado
    - Identificar padrões de comportamento
    - Classificar tipo de usuário
    """

    def calculate_profile(self, user: User, ratings: List[Rating]) -> UserProfile:
        """
        Calcula perfil completo do usuário.

        Args:
            user: entidade User
            ratings: lista de ratings do usuário

        Returns:
            UserProfile completo
        """
        if not ratings:
            return self._empty_profile(user)

        # Calcula métricas
        favorite_genres = self._extract_favorite_genres(ratings)
        genre_affinity = self._calculate_genre_affinity(ratings)
        rating_distribution = self._calculate_rating_distribution(ratings)
        avg_rating = sum(float(r.score) for r in ratings) / len(ratings)
        rating_variance = self._calculate_variance(ratings, avg_rating)

        # Classifica comportamento
        is_generous = avg_rating >= 4.0
        is_critical = avg_rating <= 3.0

        # Calcula scores
        activity_score = self._calculate_activity_score(user, ratings)
        diversity_score = self._calculate_diversity_score(genre_affinity)
        engagement_level = self._classify_engagement(activity_score)

        return UserProfile(
            user=user,
            favorite_genres=favorite_genres,
            genre_affinity=genre_affinity,
            rating_distribution=rating_distribution,
            avg_rating=round(avg_rating, 2),
            rating_variance=round(rating_variance, 2),
            is_generous_rater=is_generous,
            is_critical_rater=is_critical,
            activity_score=round(activity_score, 2),
            diversity_score=round(diversity_score, 2),
            engagement_level=engagement_level,
        )

    def _empty_profile(self, user: User) -> UserProfile:
        """Perfil vazio para usuário sem ratings"""
        return UserProfile(
            user=user,
            favorite_genres=[],
            genre_affinity={},
            rating_distribution={},
            avg_rating=0.0,
            rating_variance=0.0,
            is_generous_rater=False,
            is_critical_rater=False,
            activity_score=0.0,
            diversity_score=0.0,
            engagement_level="none",
        )

    def _extract_favorite_genres(self, ratings: List[Rating], top_n: int = 5) -> List[str]:
        """
        Extrai gêneros favoritos baseado em ratings positivos.

        Lógica:
        - Considera apenas ratings >= 4.0
        - Conta frequência de gêneros
        - Retorna top N
        """
        # Nota: Esta implementação é simplificada
        # Na prática, seria melhor buscar genres dos movies dos ratings
        # Por enquanto, retorna lista vazia (vai ser implementado na Application layer)
        return []

    def _calculate_genre_affinity(self, ratings: List[Rating]) -> Dict[str, float]:
        """
        Calcula afinidade com cada gênero.

        Fórmula:
        - Para cada gênero, avg de ratings de filmes desse gênero
        - Normalizado 0-1
        """
        # Implementação simplificada
        # Vai ser expandido na Application layer com acesso a movies
        return {}

    def _calculate_rating_distribution(self, ratings: List[Rating]) -> Dict[int, int]:
        """
        Distribução de ratings (1-5 stars).

        Returns:
            {1: count, 2: count, ..., 5: count}
        """
        distribution = Counter()
        for rating in ratings:
            star = int(float(rating.score))
            distribution[star] += 1

        # Garante todas as estrelas no dict
        for i in range(1, 6):
            if i not in distribution:
                distribution[i] = 0

        return dict(distribution)

    def _calculate_variance(self, ratings: List[Rating], avg: float) -> float:
        """
        Calcula variância dos ratings.

        Alta variância = usuário é inconsistente
        Baixa variância = usuário é consistente
        """
        if len(ratings) < 2:
            return 0.0

        squared_diffs = [(float(r.score) - avg) ** 2 for r in ratings]
        variance = sum(squared_diffs) / len(ratings)

        return variance

    def _calculate_activity_score(self, user: User, ratings: List[Rating]) -> float:
        """
        Score de atividade do usuário (0-1).

        Considera:
        - Número de ratings
        - Recência de atividade
        """
        # Componente 1: Número de ratings (logarítmico)
        import math

        n_ratings = len(ratings)
        rating_score = min(1.0, math.log(n_ratings + 1) / math.log(100))

        # Componente 2: Recência (ativo nos últimos 30 dias = 1.0)
        recency_score = 1.0 if user.is_active_user() else 0.5

        # Média ponderada (60% ratings, 40% recência)
        activity_score = (0.6 * rating_score) + (0.4 * recency_score)

        return activity_score

    def _calculate_diversity_score(self, genre_affinity: Dict[str, float]) -> float:
        """
        Score de diversidade de gêneros (0-1).

        Alta diversidade = gosta de muitos gêneros diferentes
        Baixa diversidade = foca em poucos gêneros

        Usa Shannon Entropy normalizado.
        """
        if not genre_affinity:
            return 0.0

        import math

        # Shannon Entropy
        total = sum(genre_affinity.values())
        if total == 0:
            return 0.0

        probabilities = [v / total for v in genre_affinity.values()]
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

        # Normaliza (max entropy = log2(n_genres))
        max_entropy = math.log2(len(genre_affinity))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        return normalized_entropy

    def _classify_engagement(self, activity_score: float) -> str:
        """
        Classifica nível de engajamento.

        Args:
            activity_score: score 0-1

        Returns:
            "low", "medium", "high"
        """
        if activity_score >= 0.7:
            return "high"
        elif activity_score >= 0.4:
            return "medium"
        else:
            return "low"
