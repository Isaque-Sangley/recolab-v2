"""
Ratings Router

Endpoints relacionados a avaliações (CRUD completo).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..dependencies import get_rating_service, get_recommendation_service
from ...application.services import RatingApplicationService, RecommendationApplicationService
from ...application.dtos import (
    RatingDTO,
    CreateRatingRequest,
    UpdateRatingRequest,
    DeleteRatingRequest
)


router = APIRouter(prefix="/ratings", tags=["ratings"])


# Pydantic models para request/response
class CreateRatingBody(BaseModel):
    """Body para criar rating"""
    user_id: int = Field(..., description="User ID")
    movie_id: int = Field(..., description="Movie ID")
    score: float = Field(..., ge=0.5, le=5.0, description="Rating score (0.5-5.0, increments of 0.5)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "movie_id": 123,
                "score": 4.5
            }
        }


@router.post("/", response_model=RatingDTO, status_code=status.HTTP_201_CREATED)
async def create_rating(
    body: CreateRatingBody,
    rating_service: RatingApplicationService = Depends(get_rating_service),
    recommendation_service: RecommendationApplicationService = Depends(get_recommendation_service)
):
    """
    ⭐ **CRIAR RATING**
    
    Cria novo rating (avaliação de usuário para filme).
    
    Use case: Usuário avalia um filme pela primeira vez.
    
    Side effects:
    - Atualiza estatísticas do usuário (n_ratings, avg_rating)
    - Atualiza estatísticas do filme (rating_count, avg_rating)
    - Invalida cache de recomendações
    - Publica evento RatingCreated (para analytics)
    
    Args:
        body: dados do rating (user_id, movie_id, score)
    
    Returns:
        RatingDTO criado
    
    Example:
        POST /api/v1/ratings/
        {
            "user_id": 1,
            "movie_id": 123,
            "score": 4.5
        }
    """
    request = CreateRatingRequest(
        user_id=body.user_id,
        movie_id=body.movie_id,
        score=body.score
    )
    
    try:
        rating = await rating_service.create_rating(request)
        
        # Invalida cache de recomendações do usuário
        await recommendation_service.invalidate_user_cache(body.user_id)
        
        return rating
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/", response_model=RatingDTO)
async def update_rating(
    user_id: int = Query(..., description="User ID"),
    movie_id: int = Query(..., description="Movie ID"),
    score: float = Query(..., ge=0.5, le=5.0, description="New rating score (0.5-5.0)"),
    rating_service: RatingApplicationService = Depends(get_rating_service),
    recommendation_service: RecommendationApplicationService = Depends(get_recommendation_service)
):
    """
    🔄 **ATUALIZAR RATING**
    
    Atualiza o rating de um usuário para um filme.
    
    Use case: Usuário muda sua avaliação de um filme.
    
    Args:
        user_id: ID do usuário
        movie_id: ID do filme
        score: Nova nota (0.5 a 5.0, incrementos de 0.5)
    
    Returns:
        RatingDTO atualizado
    
    Example:
        PUT /api/v1/ratings/?user_id=1&movie_id=123&score=5.0
    """
    request = UpdateRatingRequest(
        user_id=user_id,
        movie_id=movie_id,
        score=score
    )
    
    try:
        rating = await rating_service.update_rating(request)
        
        if not rating:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rating not found for user {user_id} and movie {movie_id}"
            )
        
        # Invalida cache
        await recommendation_service.invalidate_user_cache(user_id)
        
        return rating
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/")
async def delete_rating(
    user_id: int = Query(..., description="User ID"),
    movie_id: int = Query(..., description="Movie ID"),
    rating_service: RatingApplicationService = Depends(get_rating_service),
    recommendation_service: RecommendationApplicationService = Depends(get_recommendation_service)
):
    """
    🗑️ **DELETAR RATING**
    
    Remove o rating de um usuário para um filme.
    
    Use case: Usuário quer remover sua avaliação.
    
    Args:
        user_id: ID do usuário
        movie_id: ID do filme
    
    Returns:
        Mensagem de confirmação
    
    Example:
        DELETE /api/v1/ratings/?user_id=1&movie_id=123
    """
    request = DeleteRatingRequest(
        user_id=user_id,
        movie_id=movie_id
    )
    
    try:
        success = await rating_service.delete_rating(request)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rating not found for user {user_id} and movie {movie_id}"
            )
        
        # Invalida cache
        await recommendation_service.invalidate_user_cache(user_id)
        
        return {
            "message": "Rating deleted successfully",
            "user_id": user_id,
            "movie_id": movie_id,
            "status": "deleted"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/user/{user_id}", response_model=List[RatingDTO])
async def get_user_ratings(
    user_id: int,
    limit: int = Query(100, le=500, description="Max results"),
    service: RatingApplicationService = Depends(get_rating_service)
):
    """
    Lista todos os ratings de um usuário.
    
    Args:
        user_id: ID do usuário
        limit: limite de resultados (max 500)
    
    Returns:
        Lista de RatingDTO
    """
    ratings = await service.get_user_ratings(user_id, limit)
    return ratings


@router.get("/movie/{movie_id}", response_model=List[RatingDTO])
async def get_movie_ratings(
    movie_id: int,
    limit: int = Query(100, le=500, description="Max results"),
    service: RatingApplicationService = Depends(get_rating_service)
):
    """
    Lista todos os ratings de um filme.
    
    Args:
        movie_id: ID do filme
        limit: limite de resultados (max 500)
    
    Returns:
        Lista de RatingDTO
    """
    ratings = await service.get_movie_ratings(movie_id, limit)
    return ratings


@router.get("/{user_id}/{movie_id}", response_model=RatingDTO)
async def get_rating(
    user_id: int,
    movie_id: int,
    service: RatingApplicationService = Depends(get_rating_service)
):
    """
    Obtém rating específico (user + movie).
    
    Args:
        user_id: ID do usuário
        movie_id: ID do filme
    
    Returns:
        RatingDTO
    """
    rating = await service.get_rating(user_id, movie_id)
    
    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    
    return rating


@router.get("/stats/overview")
async def get_rating_stats(
    service: RatingApplicationService = Depends(get_rating_service)
):
    """
    📊 **ESTATÍSTICAS GERAIS**
    
    Estatísticas gerais de ratings do sistema.
    
    Returns:
        Dict com estatísticas:
        - total_ratings: número total de avaliações
        - unique_users: usuários únicos
        - unique_movies: filmes únicos
        - avg_rating: média global
        - rating_distribution: distribuição por estrelas
        - most_rated_movies: top filmes mais avaliados
        - most_active_users: top usuários mais ativos
    """
    stats = await service.get_rating_stats()
    return stats