"""
User Queries

Queries são operações de READ (não modificam estado).
CQRS pattern: separação entre Commands (write) e Queries (read).
"""

from typing import List, Optional

from ...domain.repositories import IRatingRepository, IUserRepository
from ...domain.services import UserProfileService
from ...domain.value_objects import UserId
from ..dtos import UserDTO, UserProfileDTO


class GetUserByIdQuery:
    """Query: Buscar usuário por ID"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int) -> Optional[UserDTO]:
        """
        Executa query.

        Args:
            user_id: ID do usuário

        Returns:
            UserDTO ou None
        """
        user = await self.user_repository.find_by_id(UserId(user_id))

        if not user:
            return None

        # Converte para DTO
        return UserDTO(
            id=int(user.id),
            created_at=user.created_at.value.isoformat(),
            n_ratings=user.n_ratings,
            avg_rating=user.avg_rating,
            last_activity=user.last_activity.value.isoformat() if user.last_activity else None,
            favorite_genres=user.favorite_genres,
            user_type=user.classify_type(),
            activity_score=user.calculate_activity_score(),
            is_active=user.is_active_user(),
        )


class GetUserProfileQuery:
    """Query: Buscar perfil completo do usuário"""

    def __init__(
        self,
        user_repository: IUserRepository,
        rating_repository: IRatingRepository,
        user_profile_service: UserProfileService,
    ):
        self.user_repository = user_repository
        self.rating_repository = rating_repository
        self.user_profile_service = user_profile_service

    async def execute(self, user_id: int) -> Optional[UserProfileDTO]:
        """
        Executa query.

        Retorna perfil rico com estatísticas.

        Args:
            user_id: ID do usuário

        Returns:
            UserProfileDTO ou None
        """
        # Busca user
        user = await self.user_repository.find_by_id(UserId(user_id))
        if not user:
            return None

        # Busca ratings
        ratings = await self.rating_repository.find_by_user(UserId(user_id))

        # Calcula perfil usando domain service
        profile = self.user_profile_service.calculate_profile(user, ratings)

        # Converte para DTO
        user_dto = UserDTO(
            id=int(user.id),
            created_at=user.created_at.value.isoformat(),
            n_ratings=user.n_ratings,
            avg_rating=user.avg_rating,
            last_activity=user.last_activity.value.isoformat() if user.last_activity else None,
            favorite_genres=user.favorite_genres,
            user_type=user.classify_type(),
            activity_score=user.calculate_activity_score(),
            is_active=user.is_active_user(),
        )

        # Determina estratégia recomendada
        from ...domain.services import RecommendationStrategyService

        strategy_service = RecommendationStrategyService()
        strategy_rec = strategy_service.decide_strategy(user)

        return UserProfileDTO(
            user=user_dto,
            rating_distribution=profile.rating_distribution,
            rating_variance=profile.rating_variance,
            is_generous_rater=profile.is_generous_rater,
            is_critical_rater=profile.is_critical_rater,
            diversity_score=profile.diversity_score,
            engagement_level=profile.engagement_level,
            recommended_strategy=strategy_rec.strategy.value,
            cf_weight=strategy_rec.cf_weight,
            cb_weight=strategy_rec.cb_weight,
        )


class ListUsersQuery:
    """Query: Listar usuários"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(
        self, limit: int = 100, offset: int = 0, user_type: Optional[str] = None
    ) -> List[UserDTO]:
        """
        Executa query.

        Args:
            limit: limite de resultados
            offset: offset para paginação
            user_type: filtrar por tipo (opcional)

        Returns:
            Lista de UserDTO
        """
        if user_type:
            users = await self.user_repository.find_by_type(user_type, limit)
        else:
            users = await self.user_repository.find_all(limit, offset)

        return [
            UserDTO(
                id=int(u.id),
                created_at=u.created_at.value.isoformat(),
                n_ratings=u.n_ratings,
                avg_rating=u.avg_rating,
                last_activity=u.last_activity.value.isoformat() if u.last_activity else None,
                favorite_genres=u.favorite_genres,
                user_type=u.classify_type(),
                activity_score=u.calculate_activity_score(),
                is_active=u.is_active_user(),
            )
            for u in users
        ]


class GetUserStatsQuery:
    """Query: Estatísticas gerais de usuários"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository

    async def execute(self) -> dict:
        """Executa query"""
        return await self.user_repository.get_user_stats()
