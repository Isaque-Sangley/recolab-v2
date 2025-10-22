"""
Domain Services Package

Domain Services contêm lógica de negócio que:
- Não pertence a nenhuma Entity específica
- Coordena múltiplas Entities
- É stateless (sem estado próprio)

Diferença entre Domain Service e Application Service:
- Domain Service: lógica de NEGÓCIO pura
- Application Service: orquestração e coordenação

Domain Services disponíveis:
- RecommendationStrategyService: decide estratégia de recomendação
- UserProfileService: calcula perfil detalhado do usuário
- DiversityService: calcula e otimiza diversidade

Características:
- Stateless (não mantém estado)
- Testáveis (lógica pura)
- Reutilizáveis
- Focados no domínio
"""

from .diversity_service import DiversityMetrics, DiversityService
from .recommendation_strategy_service import (
    RecommendationStrategyService,
    StrategyRecommendation,
    StrategyType,
)
from .user_profile_service import UserProfile, UserProfileService

__all__ = [
    # Recommendation Strategy
    "RecommendationStrategyService",
    "StrategyType",
    "StrategyRecommendation",
    # User Profile
    "UserProfileService",
    "UserProfile",
    # Diversity
    "DiversityService",
    "DiversityMetrics",
]
