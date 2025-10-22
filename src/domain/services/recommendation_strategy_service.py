"""
Recommendation Strategy Service

Decide qual estratégia de recomendação usar baseado no contexto do usuário.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from ..entities import User
from ..value_objects import UserId


class StrategyType(str, Enum):
    """Tipos de estratégia de recomendação"""

    POPULAR = "popular"  # Cold start - usuários novos
    GENRE_BASED = "genre_based"  # Poucos ratings - usa gêneros favoritos
    CONTENT_BASED = "content_based"  # CB dominante
    COLLABORATIVE = "collaborative"  # CF dominante
    HYBRID = "hybrid"  # Balanceado CF + CB
    MULTI_STAGE = "multi_stage"  # Pipeline completo (Netflix-style)


@dataclass
class StrategyRecommendation:
    """
    Recomendação de qual estratégia usar.

    Inclui explicação e pesos sugeridos.
    """

    strategy: StrategyType
    cf_weight: float
    cb_weight: float
    confidence: float  # 0-1, confiança na decisão
    reason: str  # Explicação humanizada
    metadata: Dict[str, Any]


class RecommendationStrategyService:
    """
    Domain Service: Decisão de Estratégia de Recomendação

    Por que é Domain Service?
    - Lógica de negócio que não pertence a uma Entity específica
    - Coordena múltiplas regras de domínio
    - Não tem estado próprio (stateless)

    Responsabilidade:
    - Analisar contexto do usuário
    - Decidir melhor estratégia
    - Calcular pesos CF/CB adaptativos
    """

    # Thresholds de negócio (podem vir de config depois)
    COLD_START_THRESHOLD = 0
    NEW_USER_THRESHOLD = 5
    CASUAL_USER_THRESHOLD = 20
    ACTIVE_USER_THRESHOLD = 50
    POWER_USER_THRESHOLD = 100

    def decide_strategy(self, user: User) -> StrategyRecommendation:
        """
        Decide estratégia baseado no perfil do usuário.

        Regras de negócio:
        1. 0 ratings → POPULAR (cold start)
        2. 1-4 ratings → GENRE_BASED (usa gêneros favoritos)
        3. 5-19 ratings → CONTENT_BASED dominante (CB 70%, CF 30%)
        4. 20-49 ratings → HYBRID balanceado (CB 50%, CF 50%)
        5. 50-99 ratings → COLLABORATIVE dominante (CF 70%, CB 30%)
        6. 100+ ratings → MULTI_STAGE (pipeline completo)

        Args:
            user: entidade User com perfil completo

        Returns:
            Recomendação de estratégia
        """
        n_ratings = user.n_ratings

        # Cold Start - sem nenhum rating
        if n_ratings == self.COLD_START_THRESHOLD:
            return StrategyRecommendation(
                strategy=StrategyType.POPULAR,
                cf_weight=0.0,
                cb_weight=0.0,
                confidence=1.0,
                reason="Novo usuário sem histórico - mostrando filmes populares",
                metadata={"n_ratings": n_ratings, "user_type": "cold_start"},
            )

        # Usuário muito novo - usa gêneros se disponíveis
        if n_ratings < self.NEW_USER_THRESHOLD:
            has_genres = len(user.favorite_genres) > 0

            if has_genres:
                return StrategyRecommendation(
                    strategy=StrategyType.GENRE_BASED,
                    cf_weight=0.2,
                    cb_weight=0.8,
                    confidence=0.7,
                    reason=f"Poucos ratings ({n_ratings}) - baseado em gêneros favoritos: {', '.join(user.favorite_genres[:2])}",
                    metadata={
                        "n_ratings": n_ratings,
                        "user_type": "new",
                        "favorite_genres": user.favorite_genres,
                    },
                )
            else:
                return StrategyRecommendation(
                    strategy=StrategyType.CONTENT_BASED,
                    cf_weight=0.2,
                    cb_weight=0.8,
                    confidence=0.6,
                    reason=f"Poucos ratings ({n_ratings}) - baseado em filmes similares aos que você gostou",
                    metadata={"n_ratings": n_ratings, "user_type": "new"},
                )

        # Usuário casual - CB dominante
        if n_ratings < self.CASUAL_USER_THRESHOLD:
            return StrategyRecommendation(
                strategy=StrategyType.CONTENT_BASED,
                cf_weight=0.3,
                cb_weight=0.7,
                confidence=0.75,
                reason=f"Baseado em filmes similares aos {n_ratings} que você avaliou",
                metadata={"n_ratings": n_ratings, "user_type": "casual"},
            )

        # Usuário ativo - Hybrid balanceado
        if n_ratings < self.ACTIVE_USER_THRESHOLD:
            return StrategyRecommendation(
                strategy=StrategyType.HYBRID,
                cf_weight=0.5,
                cb_weight=0.5,
                confidence=0.85,
                reason=f"Combinando padrões de usuários similares com seus {n_ratings} filmes avaliados",
                metadata={"n_ratings": n_ratings, "user_type": "active"},
            )

        # Usuário regular - CF dominante
        if n_ratings < self.POWER_USER_THRESHOLD:
            return StrategyRecommendation(
                strategy=StrategyType.COLLABORATIVE,
                cf_weight=0.7,
                cb_weight=0.3,
                confidence=0.9,
                reason=f"Baseado em {n_ratings} avaliações e usuários com gostos similares",
                metadata={"n_ratings": n_ratings, "user_type": "regular"},
            )

        # Power user - Multi-stage pipeline completo
        return StrategyRecommendation(
            strategy=StrategyType.MULTI_STAGE,
            cf_weight=0.75,
            cb_weight=0.25,
            confidence=0.95,
            reason=f"Recomendação personalizada baseada em {n_ratings} avaliações e padrões avançados",
            metadata={"n_ratings": n_ratings, "user_type": "power_user"},
        )

    def should_use_multi_stage(self, user: User) -> bool:
        """
        Verifica se deve usar pipeline multi-stage.

        Multi-stage é mais caro computacionalmente,
        então só usa para usuários com dados suficientes.

        Args:
            user: entidade User

        Returns:
            True se deve usar multi-stage
        """
        return user.n_ratings >= self.POWER_USER_THRESHOLD

    def calculate_adaptive_weights(self, user: User) -> tuple[float, float]:
        """
        Calcula pesos adaptativos CF/CB.

        Fórmula:
        - CF weight aumenta logaritmicamente com n_ratings
        - CB weight = 1 - CF weight

        Args:
            user: entidade User

        Returns:
            (cf_weight, cb_weight)
        """
        import math

        n_ratings = user.n_ratings

        if n_ratings == 0:
            return (0.0, 0.0)  # Popular strategy

        # Função logarítmica suavizada
        # cf_weight = min(0.75, log(n_ratings + 1) / log(100))
        cf_weight = min(0.75, math.log(n_ratings + 1) / math.log(100))
        cb_weight = 1.0 - cf_weight

        return (round(cf_weight, 2), round(cb_weight, 2))

    def get_strategy_metadata(self, strategy: StrategyType) -> Dict[str, Any]:
        """
        Retorna metadata sobre uma estratégia.

        Útil para:
        - Documentação
        - UI (mostrar info ao usuário)
        - Analytics

        Args:
            strategy: tipo de estratégia

        Returns:
            Dict com metadata
        """
        metadata_map = {
            StrategyType.POPULAR: {
                "name": "Popular",
                "description": "Filmes mais populares do catálogo",
                "use_case": "Novos usuários sem histórico",
                "pros": ["Sempre funciona", "Não precisa dados do usuário"],
                "cons": ["Não personalizado", "Pode não agradar"],
            },
            StrategyType.GENRE_BASED: {
                "name": "Baseado em Gêneros",
                "description": "Filmes dos gêneros favoritos do usuário",
                "use_case": "Usuários novos com poucos ratings",
                "pros": ["Rápido", "Respeita preferências conhecidas"],
                "cons": ["Pode ser repetitivo", "Pouca descoberta"],
            },
            StrategyType.CONTENT_BASED: {
                "name": "Baseado em Conteúdo",
                "description": "Filmes similares aos que você gostou",
                "use_case": "Usuários com 5-20 ratings",
                "pros": ["Personalizado", "Explica bem", "Funciona com poucos dados"],
                "cons": ["Filter bubble", "Pouca serendipity"],
            },
            StrategyType.COLLABORATIVE: {
                "name": "Filtragem Colaborativa",
                "description": "Baseado em usuários com gostos similares",
                "use_case": "Usuários com 50+ ratings",
                "pros": ["Serendipity", "Descobre novos nichos"],
                "cons": ["Precisa muitos dados", "Cold start problem"],
            },
            StrategyType.HYBRID: {
                "name": "Híbrido",
                "description": "Combina múltiplas estratégias",
                "use_case": "Usuários com 20-50 ratings",
                "pros": ["Balanceado", "Robusto"],
                "cons": ["Mais complexo", "Mais lento"],
            },
            StrategyType.MULTI_STAGE: {
                "name": "Multi-Stage Pipeline",
                "description": "Pipeline avançado com múltiplos estágios",
                "use_case": "Power users (100+ ratings)",
                "pros": ["Máxima qualidade", "Diversidade", "Personalização"],
                "cons": ["Computacionalmente caro"],
            },
        }

        return metadata_map.get(strategy, {})
