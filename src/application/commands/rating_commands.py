"""
Rating Commands

Commands são operações de WRITE (modificam estado).
CQRS pattern: separação entre Commands (write) e Queries (read).
"""

from dataclasses import dataclass
from typing import Optional

from ...domain.entities import Rating, User
from ...domain.events import DomainEventBus, RatingCreated, RatingDeleted, RatingUpdated
from ...domain.repositories import IMovieRepository, IRatingRepository, IUserRepository
from ...domain.value_objects import MovieId, RatingScore, Timestamp, UserId
from ..dtos import CreateRatingRequest, DeleteRatingRequest, RatingDTO, UpdateRatingRequest


@dataclass
class CreateRatingCommand:
    """
    Command: Criar novo rating.

    Use case: Usuário avalia um filme.

    Regras de negócio:
    - User deve existir (ou criar automaticamente)
    - Movie deve existir
    - Rating deve ser válido (0.5-5.0, incrementos de 0.5)
    - Atualiza estatísticas do user
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

    async def execute(self, request: CreateRatingRequest) -> RatingDTO:
        """
        Executa comando.

        Args:
            request: request validado

        Returns:
            RatingDTO criado

        Raises:
            ValueError: se validação falhar
        """
        # Valida request
        request.validate()

        # Verifica se user existe (cria se não)
        user = await self.user_repository.find_by_id(UserId(request.user_id))
        if not user:
            # Auto-cria usuário
            user = User.create(user_id=UserId(request.user_id))
            await self.user_repository.save(user)

        # Verifica se movie existe
        movie = await self.movie_repository.find_by_id(MovieId(request.movie_id))
        if not movie:
            raise ValueError(f"Movie {request.movie_id} not found")

        # Verifica se já existe rating
        existing = await self.rating_repository.find_by_user_and_movie(
            UserId(request.user_id), MovieId(request.movie_id)
        )

        if existing:
            raise ValueError(f"Rating already exists. Use update instead.")

        # Cria rating entity
        rating = Rating(
            user_id=UserId(request.user_id),
            movie_id=MovieId(request.movie_id),
            score=RatingScore(request.score),
            timestamp=Timestamp.now(),
        )

        # Salva
        saved_rating = await self.rating_repository.save(rating)

        # Atualiza estatísticas do user
        await self._update_user_stats(user)

        # Atualiza estatísticas do movie
        await self._update_movie_stats(movie)

        # Publica evento
        if self.event_bus:
            event = RatingCreated(
                user_id=request.user_id, movie_id=request.movie_id, rating=request.score
            )
            self.event_bus.publish(event)

        # Converte para DTO
        return RatingDTO(
            user_id=int(saved_rating.user_id),
            movie_id=int(saved_rating.movie_id),
            score=float(saved_rating.score),
            timestamp=saved_rating.timestamp.value.isoformat(),
        )

    async def _update_user_stats(self, user: User) -> None:
        """Atualiza estatísticas do usuário"""
        # Busca todos os ratings do user
        ratings = await self.rating_repository.find_by_user(user.id)

        if ratings:
            # Calcula média
            avg_rating = sum(float(r.score) for r in ratings) / len(ratings)

            # Extrai gêneros favoritos (simplificado - precisaria dos movies)
            # Por ora, deixa como está

            # Atualiza user
            user.n_ratings = len(ratings)
            user.avg_rating = avg_rating
            user.mark_activity()

            await self.user_repository.save(user)

    async def _update_movie_stats(self, movie) -> None:
        """Atualiza estatísticas do filme"""
        # Busca todos os ratings do movie
        ratings = await self.rating_repository.find_by_movie(movie.id)

        if ratings:
            avg_rating = sum(float(r.score) for r in ratings) / len(ratings)

            movie.rating_count = len(ratings)
            movie.avg_rating = avg_rating

            await self.movie_repository.save(movie)


@dataclass
class UpdateRatingCommand:
    """Command: Atualizar rating existente"""

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

    async def execute(self, request: UpdateRatingRequest) -> RatingDTO:
        """Executa comando"""
        request.validate()

        # Busca rating existente
        rating = await self.rating_repository.find_by_user_and_movie(
            UserId(request.user_id), MovieId(request.movie_id)
        )

        if not rating:
            raise ValueError("Rating not found. Use create instead.")

        old_score = float(rating.score)

        # Atualiza score
        rating.score = RatingScore(request.score)
        rating.timestamp = Timestamp.now()

        # Salva
        saved_rating = await self.rating_repository.save(rating)

        # Atualiza stats (user e movie)
        user = await self.user_repository.find_by_id(UserId(request.user_id))
        if user:
            await self._update_user_stats(user)

        movie = await self.movie_repository.find_by_id(MovieId(request.movie_id))
        if movie:
            await self._update_movie_stats(movie)

        # Publica evento
        if self.event_bus:
            event = RatingUpdated(
                user_id=request.user_id,
                movie_id=request.movie_id,
                old_rating=old_score,
                new_rating=request.score,
            )
            self.event_bus.publish(event)

        return RatingDTO(
            user_id=int(saved_rating.user_id),
            movie_id=int(saved_rating.movie_id),
            score=float(saved_rating.score),
            timestamp=saved_rating.timestamp.value.isoformat(),
        )

    async def _update_user_stats(self, user: User) -> None:
        """Atualiza estatísticas do usuário"""
        ratings = await self.rating_repository.find_by_user(user.id)

        if ratings:
            avg_rating = sum(float(r.score) for r in ratings) / len(ratings)
            user.n_ratings = len(ratings)
            user.avg_rating = avg_rating
            user.mark_activity()
            await self.user_repository.save(user)

    async def _update_movie_stats(self, movie) -> None:
        """Atualiza estatísticas do filme"""
        ratings = await self.rating_repository.find_by_movie(movie.id)

        if ratings:
            avg_rating = sum(float(r.score) for r in ratings) / len(ratings)
            movie.rating_count = len(ratings)
            movie.avg_rating = avg_rating
            await self.movie_repository.save(movie)


@dataclass
class DeleteRatingCommand:
    """Command: Deletar rating"""

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

    async def execute(self, request: DeleteRatingRequest) -> bool:
        """Executa comando"""
        # Busca rating
        rating = await self.rating_repository.find_by_user_and_movie(
            UserId(request.user_id), MovieId(request.movie_id)
        )

        if not rating:
            return False

        deleted_score = float(rating.score)

        # Deleta
        success = await self.rating_repository.delete(
            (UserId(request.user_id), MovieId(request.movie_id))
        )

        if success:
            # Atualiza stats
            user = await self.user_repository.find_by_id(UserId(request.user_id))
            if user:
                await self._update_user_stats(user)

            movie = await self.movie_repository.find_by_id(MovieId(request.movie_id))
            if movie:
                await self._update_movie_stats(movie)

            # Publica evento
            if self.event_bus:
                event = RatingDeleted(
                    user_id=request.user_id, movie_id=request.movie_id, rating=deleted_score
                )
                self.event_bus.publish(event)

        return success

    async def _update_user_stats(self, user: User) -> None:
        """Atualiza estatísticas do usuário"""
        ratings = await self.rating_repository.find_by_user(user.id)

        if ratings:
            avg_rating = sum(float(r.score) for r in ratings) / len(ratings)
            user.n_ratings = len(ratings)
            user.avg_rating = avg_rating
        else:
            user.n_ratings = 0
            user.avg_rating = 0.0

        user.mark_activity()
        await self.user_repository.save(user)

    async def _update_movie_stats(self, movie) -> None:
        """Atualiza estatísticas do filme"""
        ratings = await self.rating_repository.find_by_movie(movie.id)

        if ratings:
            avg_rating = sum(float(r.score) for r in ratings) / len(ratings)
            movie.rating_count = len(ratings)
            movie.avg_rating = avg_rating
        else:
            movie.rating_count = 0
            movie.avg_rating = 0.0

        await self.movie_repository.save(movie)
