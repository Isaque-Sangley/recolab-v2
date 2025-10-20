"""
User Application Service

Orquestra use cases relacionados a usuários.
Expõe API limpa para camada de apresentação.
"""

from typing import List, Optional

from ...domain.repositories import IUserRepository, IRatingRepository
from ...domain.services import UserProfileService
from ..dtos import CreateUserRequest, UpdateUserRequest
from ..queries import (
    GetUserByIdQuery,
    GetUserProfileQuery,
    ListUsersQuery,
    GetUserStatsQuery
)
from ..dtos import UserDTO, UserProfileDTO


class UserApplicationService:
    """
    User Application Service.
    
    Responsabilidades:
    - Orquestrar Commands e Queries
    - Coordenar Domain Services
    - Gerenciar transações
    - Expor API limpa
    
    NÃO contém lógica de negócio (isso fica no Domain).
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        rating_repository: IRatingRepository
    ):
        self.user_repository = user_repository
        self.rating_repository = rating_repository
        
        # Domain Services
        self.user_profile_service = UserProfileService()
        
        # Queries
        self.get_user_query = GetUserByIdQuery(user_repository)
        self.get_profile_query = GetUserProfileQuery(
            user_repository,
            rating_repository,
            self.user_profile_service
        )
        self.list_users_query = ListUsersQuery(user_repository)
        self.get_stats_query = GetUserStatsQuery(user_repository)
    
    async def get_user(self, user_id: int) -> Optional[UserDTO]:
        """
        Obtém usuário por ID.
        
        Args:
            user_id: ID do usuário
        
        Returns:
            UserDTO ou None
        """
        return await self.get_user_query.execute(user_id)
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfileDTO]:
        """
        Obtém perfil completo do usuário.
        
        Args:
            user_id: ID do usuário
        
        Returns:
            UserProfileDTO com estatísticas completas
        """
        return await self.get_profile_query.execute(user_id)
    
    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        user_type: Optional[str] = None
    ) -> List[UserDTO]:
        """
        Lista usuários.
        
        Args:
            limit: limite de resultados
            offset: offset para paginação
            user_type: filtrar por tipo (opcional)
        
        Returns:
            Lista de UserDTO
        """
        return await self.list_users_query.execute(limit, offset, user_type)
    
    async def get_user_stats(self) -> dict:
        """
        Obtém estatísticas gerais de usuários.
        
        Returns:
            Dict com estatísticas
        """
        return await self.get_stats_query.execute()
    
    async def user_exists(self, user_id: int) -> bool:
        """
        Verifica se usuário existe.
        
        Args:
            user_id: ID do usuário
        
        Returns:
            True se existe
        """
        from ...domain.value_objects import UserId
        return await self.user_repository.exists(UserId(user_id))