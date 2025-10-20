"""
Movies Router

Endpoints relacionados a filmes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_movie_service
from ...application.services import MovieApplicationService
from ...application.dtos import MovieDTO, MovieDetailDTO, FilterMoviesRequest


router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/{movie_id}", response_model=MovieDTO)
async def get_movie(
    movie_id: int,
    service: MovieApplicationService = Depends(get_movie_service)
):
    """
    Obtém filme por ID.
    
    Args:
        movie_id: ID do filme
    
    Returns:
        MovieDTO
    """
    movie = await service.get_movie(movie_id)
    
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie {movie_id} not found"
        )
    
    return movie


@router.get("/{movie_id}/details", response_model=MovieDetailDTO)
async def get_movie_details(
    movie_id: int,
    service: MovieApplicationService = Depends(get_movie_service)
):
    """
    Obtém detalhes completos do filme.
    
    Inclui filmes similares.
    
    Args:
        movie_id: ID do filme
    
    Returns:
        MovieDetailDTO
    """
    details = await service.get_movie_details(movie_id)
    
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie {movie_id} not found"
        )
    
    return details


@router.get("/search/", response_model=List[MovieDTO])
async def search_movies(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(50, le=100, description="Max results"),
    service: MovieApplicationService = Depends(get_movie_service)
):
    """
    Busca filmes por título.
    
    Args:
        q: termo de busca (mínimo 2 caracteres)
        limit: limite de resultados (max 100)
    
    Returns:
        Lista de MovieDTO
    """
    movies = await service.search_movies(q, limit)
    return movies


@router.get("/filter/", response_model=List[MovieDTO])
async def filter_movies(
    genres: Optional[List[str]] = Query(None, description="Filter by genres"),
    min_year: Optional[int] = Query(None, description="Minimum year"),
    max_year: Optional[int] = Query(None, description="Maximum year"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    min_rating_count: Optional[int] = Query(None, ge=0, description="Minimum rating count"),
    limit: int = Query(100, le=200, description="Max results"),
    service: MovieApplicationService = Depends(get_movie_service)
):
    """
    Filtra filmes por múltiplos critérios.
    
    Args:
        genres: lista de gêneros
        min_year: ano mínimo
        max_year: ano máximo
        min_rating: rating mínimo (0-5)
        min_rating_count: mínimo de avaliações
        limit: limite de resultados
    
    Returns:
        Lista de MovieDTO
    """
    request = FilterMoviesRequest(
        genres=genres,
        min_year=min_year,
        max_year=max_year,
        min_rating=min_rating,
        min_rating_count=min_rating_count,
        limit=limit
    )
    
    movies = await service.filter_movies(request)
    return movies


@router.get("/popular/list", response_model=List[MovieDTO])
async def get_popular_movies(
    limit: int = Query(40, le=100, description="Max results"),
    service: MovieApplicationService = Depends(get_movie_service)
):
    """
    Filmes populares.
    
    Ordenado por número de avaliações.
    
    Args:
        limit: limite de resultados
    
    Returns:
        Lista de MovieDTO
    """
    movies = await service.get_popular_movies(limit)
    return movies


@router.get("/genres/list", response_model=List[str])
async def get_all_genres(
    service: MovieApplicationService = Depends(get_movie_service)
):
    """
    Todos os gêneros disponíveis.
    
    Returns:
        Lista de gêneros
    """
    genres = await service.get_all_genres()
    return genres


@router.get("/by-genre/{genre}", response_model=List[MovieDTO])
async def get_movies_by_genre(
    genre: str,
    limit: int = Query(40, le=100, description="Max results"),
    service: MovieApplicationService = Depends(get_movie_service)
):
    """
    Filmes de um gênero específico.
    
    Args:
        genre: nome do gênero
        limit: limite de resultados
    
    Returns:
        Lista de MovieDTO
    """
    movies = await service.get_movies_by_genre(genre, limit)
    return movies