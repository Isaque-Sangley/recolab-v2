"""
Recommendations Router

Endpoints de recomendação - coração do sistema!
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...application.dtos import (
    ExplainRecommendationRequest,
    ExplanationDTO,
    GetRecommendationsRequest,
    RecommendationListDTO,
)
from ...application.services import RecommendationApplicationService
from ..dependencies import get_recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# Pydantic models para request/response
class GetRecommendationsBody(BaseModel):
    """Body para obter recomendações"""

    user_id: int = Field(..., description="User ID")
    n_recommendations: int = Field(
        10, ge=1, le=100, description="Number of recommendations (1-100)"
    )
    strategy: Optional[str] = Field(
        None, description="Strategy: adaptive, collaborative, content, hybrid"
    )
    diversity_weight: float = Field(0.3, ge=0.0, le=1.0, description="Diversity weight (0-1)")
    include_explanations: bool = Field(False, description="Include explanations")
    exclude_seen: bool = Field(True, description="Exclude already rated movies")
    genres: Optional[List[str]] = Field(None, description="Filter by genres")
    min_year: Optional[int] = Field(None, description="Minimum year")
    max_year: Optional[int] = Field(None, description="Maximum year")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "n_recommendations": 10,
                "strategy": "adaptive",
                "diversity_weight": 0.3,
                "include_explanations": True,
                "exclude_seen": True,
            }
        }


@router.post("/", response_model=RecommendationListDTO)
async def get_recommendations(
    body: GetRecommendationsBody,
    service: RecommendationApplicationService = Depends(get_recommendation_service),
):
    """
        **GERADOR DE RECOMENDAÇÕES** - O endpoint principal!

        Pipeline completo:
        1. Análise de perfil do usuário
        2. Seleção de estratégia (adaptive, collaborative, content)
        3. Geração usando modelo de ML (Neural CF)
        4. Re-ranking para diversidade
        5. Enriquecimento com metadata
        6. Explicações (opcional)

        Estratégias disponíveis:
        - **adaptive**: escolhe automaticamente baseado no perfil (RECOMENDADO)
        - **collaborative**: baseado em usuários similares
        - **content**: baseado em conteúdo dos filmes
        - **hybrid**: combinação balanceada

        Perfis de usuário:
        - **cold_start** (0 ratings): filmes populares
        - **new** (1-4 ratings): baseado em gêneros favoritos
        - **casual** (5-19 ratings): content-based dominante
        - **active** (20-99 ratings): híbrido balanceado
        - **power_user** (100+ ratings): collaborative dominante

        Args:
            body: parâmetros da recomendação

        Returns:
            RecommendationListDTO com:
            - recommendations: lista de filmes recomendados
            - strategy_used: estratégia utilizada
            - cf_weight/cb_weight: pesos do modelo
            - diversity_score: score de diversidade
            - generation_time_ms: tempo de geração

        Example:
    ```json
            {
                "user_id": 1,
                "n_recommendations": 10,
                "strategy": "adaptive",
                "diversity_weight": 0.3,
                "include_explanations": true
            }
    ```
    """
    request = GetRecommendationsRequest(
        user_id=body.user_id,
        n_recommendations=body.n_recommendations,
        strategy=body.strategy,
        diversity_weight=body.diversity_weight,
        include_explanations=body.include_explanations,
        exclude_seen=body.exclude_seen,
        genres=body.genres,
        min_year=body.min_year,
        max_year=body.max_year,
    )

    try:
        recommendations = await service.get_recommendations(request)
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{user_id}", response_model=RecommendationListDTO)
async def get_recommendations_get(
    user_id: int,
    n: int = Query(10, ge=1, le=100, description="Number of recommendations"),
    strategy: Optional[str] = Query(None, description="Strategy"),
    diversity: float = Query(0.3, ge=0.0, le=1.0, description="Diversity weight"),
    explain: bool = Query(False, description="Include explanations"),
    service: RecommendationApplicationService = Depends(get_recommendation_service),
):
    """
    Get recommendations (GET variant).

    Mesma funcionalidade do POST, mas via GET para facilitar testes.

    Args:
        user_id: ID do usuário
        n: número de recomendações
        strategy: estratégia (optional)
        diversity: peso de diversidade
        explain: incluir explicações

    Returns:
        RecommendationListDTO
    """
    request = GetRecommendationsRequest(
        user_id=user_id,
        n_recommendations=n,
        strategy=strategy,
        diversity_weight=diversity,
        include_explanations=explain,
    )

    try:
        recommendations = await service.get_recommendations(request)
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/explain/{user_id}/{movie_id}", response_model=ExplanationDTO)
async def explain_recommendation(
    user_id: int,
    movie_id: int,
    service: RecommendationApplicationService = Depends(get_recommendation_service),
):
    """
        Explica por que um filme foi recomendado.

        Fornece explicação detalhada:
        - Razão principal (gêneros, popularidade, padrões)
        - Score de confiança
        - Perfil do usuário
        - Features do filme
        - Detalhes de similaridade

        Args:
            user_id: ID do usuário
            movie_id: ID do filme

        Returns:
            ExplanationDTO com explicação detalhada

        Example response:
    ```json
            {
                "user_id": 1,
                "movie_id": 123,
                "movie_title": "The Matrix",
                "primary_reason": "Este filme combina com seus gêneros favoritos: Action, Sci-Fi",
                "confidence": 0.85,
                "user_profile": {...},
                "movie_features": {...}
            }
    ```
    """
    request = ExplainRecommendationRequest(user_id=user_id, movie_id=movie_id)

    explanation = await service.explain_recommendation(request)

    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot explain recommendation for user {user_id} and movie {movie_id}",
        )

    return explanation


@router.get("/popular/list")
async def get_popular_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    service: RecommendationApplicationService = Depends(get_recommendation_service),
):
    """
    Recomendações populares (cold start).

    Usado quando não há usuário autenticado.
    Retorna filmes mais populares do catálogo.

    Args:
        limit: número de resultados

    Returns:
        Lista de filmes populares
    """
    recommendations = await service.get_popular_recommendations(limit)
    return {
        "recommendations": recommendations,
        "source": "popular",
        "description": "Most popular movies in the catalog",
    }


@router.get("/trending/list")
async def get_trending_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    service: RecommendationApplicationService = Depends(get_recommendation_service),
):
    """
    Recomendações em alta (trending).

    Baseado em atividade recente (últimos 7 dias).
    Filmes com mais interações recentes.

    Args:
        limit: número de resultados

    Returns:
        Lista de filmes trending
    """
    recommendations = await service.get_trending_recommendations(limit)
    return {
        "recommendations": recommendations,
        "source": "trending",
        "description": "Movies with most recent activity (last 7 days)",
    }
