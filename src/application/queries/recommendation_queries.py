"""
Recommendation Queries
"""

from datetime import datetime
from typing import List, Optional

from ...domain.events import ModelType
from ...domain.repositories import IMovieRepository, IRatingRepository, IUserRepository
from ...domain.services import DiversityService, RecommendationStrategyService
from ...domain.value_objects import MovieId, UserId
from ...infrastructure.ml import FeatureStore, ModelServer
from ..dtos import (
    ExplainRecommendationRequest,
    ExplanationDTO,
    GetRecommendationsRequest,
    RecommendationDTO,
    RecommendationListDTO,
)


class GetRecommendationsQuery:
    """
    Query: Gerar recomendações para usuário.

    Pipeline completo:
    1. Analisa perfil do usuário
    2. Decide estratégia
    3. Gera recomendações (modelo ML)
    4. Aplica diversidade
    5. Enriquece com metadata
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        movie_repository: IMovieRepository,
        rating_repository: IRatingRepository,
        model_server: ModelServer,
        feature_store: FeatureStore,
        strategy_service: RecommendationStrategyService,
        diversity_service: DiversityService,
    ):
        self.user_repository = user_repository
        self.movie_repository = movie_repository
        self.rating_repository = rating_repository
        self.model_server = model_server
        self.feature_store = feature_store
        self.strategy_service = strategy_service
        self.diversity_service = diversity_service

    async def execute(self, request: GetRecommendationsRequest) -> RecommendationListDTO:
        """
        Executa query.

        Args:
            request: request de recomendações

        Returns:
            RecommendationListDTO com recomendações
        """
        start_time = datetime.now()

        # 1. Busca perfil do usuário
        user = await self.user_repository.find_by_id(UserId(request.user_id))
        if not user:
            raise ValueError(f"User {request.user_id} not found")

        # 2. Decide estratégia
        strategy_rec = self.strategy_service.decide_strategy(user)

        # Sobrescreve se request especificou
        if request.strategy:
            # TODO: mapear string para StrategyType
            pass

        # 3. Busca itens já vistos (para exclusão)
        exclude_items = []
        if request.exclude_seen:
            ratings = await self.rating_repository.find_by_user(UserId(request.user_id))
            exclude_items = [int(r.movie_id) for r in ratings]

        # 4. Gera recomendações usando modelo
        recommendations = await self.model_server.recommend(
            model_type=ModelType.NEURAL_CF,  # TODO: decidir baseado na estratégia
            user_id=request.user_id,
            n_recommendations=request.n_recommendations * 2,  # Pega mais para diversificar
            exclude_items=exclude_items,
            use_cache=True,
        )

        # 5. Aplica diversidade (se solicitado)
        if request.diversity_weight > 0:
            # Busca movies para diversidade
            movie_ids = [int(rec.movie_id) for rec in recommendations]
            movies = []
            for movie_id in movie_ids:
                movie = await self.movie_repository.find_by_id(MovieId(movie_id))
                if movie:
                    movies.append(movie)

            # Re-ranqueia para diversidade
            recommendations = self.diversity_service.rerank_for_diversity(
                recommendations=recommendations,
                movies=movies,
                diversity_weight=request.diversity_weight,
            )

        # Limita ao número solicitado
        recommendations = recommendations[: request.n_recommendations]

        # 6. Enriquece com metadata dos filmes
        enriched_recommendations = []
        movie_ids_for_diversity = []

        for rec in recommendations:
            movie = await self.movie_repository.find_by_id(rec.movie_id)

            if movie:
                movie_ids_for_diversity.extend(movie.genres)

                # Gera explicação (se solicitado)
                explanation = None
                if request.include_explanations:
                    explanation = self._generate_explanation(user, movie, strategy_rec.reason)

                rec_dto = RecommendationDTO(
                    movie_id=int(rec.movie_id),
                    score=float(rec.score),
                    rank=rec.rank,
                    source=rec.source.value,
                    movie_title=movie.title,
                    movie_genres=movie.genres,
                    explanation=explanation,
                    metadata=rec.metadata,
                )

                enriched_recommendations.append(rec_dto)

        # 7. Calcula diversidade
        unique_genres = list(set(movie_ids_for_diversity))
        diversity_score = len(unique_genres) / max(1, len(enriched_recommendations))

        # 8. Calcula tempo de geração
        generation_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        return RecommendationListDTO(
            user_id=request.user_id,
            recommendations=enriched_recommendations,
            strategy_used=strategy_rec.strategy.value,
            cf_weight=strategy_rec.cf_weight,
            cb_weight=strategy_rec.cb_weight,
            user_type=user.classify_type(),
            diversity_score=round(diversity_score, 3),
            unique_genres=unique_genres,
            generation_time_ms=round(generation_time_ms, 2),
        )

    def _generate_explanation(self, user, movie, base_reason: str) -> str:
        """Gera explicação humanizada"""
        # Verifica overlap de gêneros
        user_genres = set(user.favorite_genres)
        movie_genres = set(movie.genres)

        common_genres = user_genres.intersection(movie_genres)

        if common_genres:
            genres_str = ", ".join(list(common_genres)[:2])
            return f"Recomendado porque você gosta de {genres_str}"

        return base_reason


class ExplainRecommendationQuery:
    """Query: Explicar por que um filme foi recomendado"""

    def __init__(
        self,
        user_repository: IUserRepository,
        movie_repository: IMovieRepository,
        rating_repository: IRatingRepository,
    ):
        self.user_repository = user_repository
        self.movie_repository = movie_repository
        self.rating_repository = rating_repository

    async def execute(self, request: ExplainRecommendationRequest) -> Optional[ExplanationDTO]:
        """
        Executa query.

        Gera explicação detalhada.
        """
        # Busca user e movie
        user = await self.user_repository.find_by_id(UserId(request.user_id))
        movie = await self.movie_repository.find_by_id(MovieId(request.movie_id))

        if not user or not movie:
            return None

        # Analisa similaridade de gêneros
        user_genres = set(user.favorite_genres)
        movie_genres = set(movie.genres)

        common_genres = user_genres.intersection(movie_genres)
        genre_match_score = len(common_genres) / max(1, len(movie_genres))

        # Gera razão principal
        if common_genres:
            genres_str = ", ".join(list(common_genres))
            primary_reason = f"Este filme combina com seus gêneros favoritos: {genres_str}"
        elif movie.is_popular():
            primary_reason = "Este é um filme muito popular e bem avaliado"
        else:
            primary_reason = "Recomendado com base em padrões de usuários similares"

        # Monta explicação
        return ExplanationDTO(
            user_id=request.user_id,
            movie_id=request.movie_id,
            movie_title=movie.title,
            primary_reason=primary_reason,
            confidence=genre_match_score,
            user_profile={
                "favorite_genres": user.favorite_genres,
                "n_ratings": user.n_ratings,
                "avg_rating": user.avg_rating,
                "user_type": user.classify_type(),
            },
            movie_features={
                "genres": movie.genres,
                "avg_rating": movie.avg_rating,
                "rating_count": movie.rating_count,
                "popularity_score": movie.calculate_popularity_score(),
            },
            similarity_details={
                "common_genres": list(common_genres),
                "genre_match_score": round(genre_match_score, 3),
            },
        )
