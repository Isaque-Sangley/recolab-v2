"""
Recommendation DTOs
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RecommendationDTO:
    """DTO de recomendação"""

    movie_id: int
    score: float
    rank: int
    source: str

    # Metadata
    movie_title: Optional[str] = None
    movie_genres: Optional[List[str]] = None
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "movie_id": self.movie_id,
            "score": self.score,
            "rank": self.rank,
            "source": self.source,
            "movie_title": self.movie_title,
            "movie_genres": self.movie_genres,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


@dataclass
class RecommendationListDTO:
    """Lista de recomendações com metadata"""

    user_id: int
    recommendations: List[RecommendationDTO]

    # Metadata da geração
    strategy_used: str
    cf_weight: float
    cb_weight: float
    user_type: str

    # Métricas de diversidade
    diversity_score: float
    unique_genres: List[str]

    # Performance
    generation_time_ms: float

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "strategy_used": self.strategy_used,
            "cf_weight": self.cf_weight,
            "cb_weight": self.cb_weight,
            "user_type": self.user_type,
            "diversity_score": self.diversity_score,
            "unique_genres": self.unique_genres,
            "generation_time_ms": self.generation_time_ms,
        }


@dataclass
class GetRecommendationsRequest:
    """Request para obter recomendações"""

    user_id: int
    n_recommendations: int = 10

    # Opções
    strategy: Optional[str] = None  # "adaptive", "collaborative", "content", "hybrid"
    diversity_weight: float = 0.3
    include_explanations: bool = False
    exclude_seen: bool = True

    # Filtros
    genres: Optional[List[str]] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None


@dataclass
class ExplainRecommendationRequest:
    """Request para explicar recomendação"""

    user_id: int
    movie_id: int


@dataclass
class ExplanationDTO:
    """DTO de explicação de recomendação"""

    user_id: int
    movie_id: int
    movie_title: str

    # Explicação
    primary_reason: str
    confidence: float

    # Detalhes
    user_profile: Dict[str, Any]
    movie_features: Dict[str, Any]
    similarity_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "movie_title": self.movie_title,
            "primary_reason": self.primary_reason,
            "confidence": self.confidence,
            "user_profile": self.user_profile,
            "movie_features": self.movie_features,
            "similarity_details": self.similarity_details,
        }
