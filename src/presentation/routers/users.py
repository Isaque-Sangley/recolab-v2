"""
Users Router

Endpoints relacionados a usuários.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.dtos import UserDTO, UserProfileDTO
from ...application.services import UserApplicationService
from ..dependencies import get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserDTO)
async def get_user(user_id: int, service: UserApplicationService = Depends(get_user_service)):
    """
    Obtém usuário por ID.

    Args:
        user_id: ID do usuário

    Returns:
        UserDTO
    """
    user = await service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    return user


@router.get("/{user_id}/profile", response_model=UserProfileDTO)
async def get_user_profile(
    user_id: int, service: UserApplicationService = Depends(get_user_service)
):
    """
    Obtém perfil completo do usuário.

    Inclui estatísticas detalhadas e recomendação de estratégia.

    Args:
        user_id: ID do usuário

    Returns:
        UserProfileDTO
    """
    profile = await service.get_user_profile(user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
        )

    return profile


@router.get("/", response_model=List[UserDTO])
async def list_users(
    limit: int = 100,
    offset: int = 0,
    user_type: Optional[str] = None,
    service: UserApplicationService = Depends(get_user_service),
):
    """
    Lista usuários.

    Args:
        limit: limite de resultados (max 100)
        offset: offset para paginação
        user_type: filtrar por tipo (cold_start, new, casual, active, power_user)

    Returns:
        Lista de UserDTO
    """
    if limit > 100:
        limit = 100

    users = await service.list_users(limit, offset, user_type)
    return users


@router.get("/stats/overview")
async def get_user_stats(service: UserApplicationService = Depends(get_user_service)):
    """
    Estatísticas gerais de usuários.

    Returns:
        Dict com estatísticas
    """
    stats = await service.get_user_stats()
    return stats
