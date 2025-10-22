"""
Rating Application Service
"""

from typing import List, Optional

from ...domain.events import DomainEventBus
from ...domain.repositories import IMovieRepository, IRatingRepository, IUserRepository
from ..commands import CreateRatingCommand, DeleteRatingCommand, UpdateRatingCommand
from ..dtos import CreateRatingRequest, DeleteRatingRequest, RatingDTO, UpdateRatingRequest


class RatingApplicationService:
    """
    Rating Application Service.

    Orquestra use cases relacionados a ratings.
    """

    def __init__(
        self,
        rating_repository: IRatingRepository,
        user_repository: IUserRepository,
        movie_repository: IMovieRepository,
        event_bus: Optional[DomainEventBus] = None,
    ):
        self.rating_repository = rating_repository
        self.user_repository = user_repository
        self.movie_repository = movie_repository
        self.event_bus = event_bus

        # Commands
        self.create_command = CreateRatingCommand(
            rating_repository, user_repository, movie_repository, event_bus
        )

        self.update_command = UpdateRatingCommand(
            rating_repository, user_repository, movie_repository, event_bus
        )

        self.delete_command = DeleteRatingCommand(
            rating_repository, user_repository, movie_repository, event_bus
        )

    async def create_rating(self, request: CreateRatingRequest) -> RatingDTO:
        """
        Cria novo rating.

        Use case: Usuário avalia um filme.

        Args:
            request: request de criação

        Returns:
            RatingDTO criado

        Raises:
            ValueError: se validação falhar
        """
        return await self.create_command.execute(request)

    async def update_rating(self, request: UpdateRatingRequest) -> RatingDTO:
        """
        Atualiza rating existente.

        Args:
            request: request de atualização

        Returns:
            RatingDTO atualizado

        Raises:
            ValueError: se rating não existir
        """
        return await self.update_command.execute(request)

    async def delete_rating(self, request: DeleteRatingRequest) -> bool:
        """
        Remove rating.

        Args:
            request: request de remoção

        Returns:
            True se removido com sucesso
        """
        return await self.delete_command.execute(request)

    async def get_user_ratings(self, user_id: int) -> List[RatingDTO]:
        """
        Obtém todos os ratings de um usuário.

        Args:
            user_id: ID do usuário

        Returns:
            Lista de RatingDTO
        """
        from ...domain.value_objects import UserId

        ratings = await self.rating_repository.find_by_user(UserId(user_id))

        return [
            RatingDTO(
                user_id=int(r.user_id),
                movie_id=int(r.movie_id),
                score=float(r.score),
                timestamp=r.timestamp.value.isoformat(),
            )
            for r in ratings
        ]

    async def get_movie_ratings(self, movie_id: int) -> List[RatingDTO]:
        """
        Obtém todos os ratings de um filme.

        Args:
            movie_id: ID do filme

        Returns:
            Lista de RatingDTO
        """
        from ...domain.value_objects import MovieId

        ratings = await self.rating_repository.find_by_movie(MovieId(movie_id))

        return [
            RatingDTO(
                user_id=int(r.user_id),
                movie_id=int(r.movie_id),
                score=float(r.score),
                timestamp=r.timestamp.value.isoformat(),
            )
            for r in ratings
        ]

    async def get_rating(self, user_id: int, movie_id: int) -> Optional[RatingDTO]:
        """
        Obtém rating específico.

        Args:
            user_id: ID do usuário
            movie_id: ID do filme

        Returns:
            RatingDTO ou None
        """
        from ...domain.value_objects import MovieId, UserId

        rating = await self.rating_repository.find_by_user_and_movie(
            UserId(user_id), MovieId(movie_id)
        )

        if not rating:
            return None

        return RatingDTO(
            user_id=int(rating.user_id),
            movie_id=int(rating.movie_id),
            score=float(rating.score),
            timestamp=rating.timestamp.value.isoformat(),
        )

    async def get_rating_stats(self) -> dict:
        """
        Obtém estatísticas gerais de ratings.

        Returns:
            Dict com estatísticas
        """
        return await self.rating_repository.get_rating_stats()
