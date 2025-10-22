"""
Recommendation Application Service

Orquestra geração de recomendações.
Pipeline completo com ML.
"""

from typing import List, Optional

from ...domain.repositories import (
    IMovieRepository,
    IRatingRepository,
    IRecommendationRepository,
    IUserRepository,
)
from ...domain.services import DiversityService, RecommendationStrategyService
from ...infrastructure.ml import FeatureStore, ModelServer
from ..dtos import (
    ExplainRecommendationRequest,
    ExplanationDTO,
    GetRecommendationsRequest,
    RecommendationListDTO,
)
from ..queries import ExplainRecommendationQuery, GetRecommendationsQuery


class RecommendationApplicationService:
    """
    Recommendation Application Service.

    Orquestra pipeline completo de recomendação:
    1. Análise de perfil
    2. Seleção de estratégia
    3. Geração (ML)
    4. Diversificação
    5. Explicação
    6. Persistência
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        movie_repository: IMovieRepository,
        rating_repository: IRatingRepository,
        recommendation_repository: IRecommendationRepository,
        model_server: ModelServer,
        feature_store: FeatureStore,
    ):
        self.user_repository = user_repository
        self.movie_repository = movie_repository
        self.rating_repository = rating_repository
        self.recommendation_repository = recommendation_repository
        self.model_server = model_server
        self.feature_store = feature_store

        # Domain Services
        self.strategy_service = RecommendationStrategyService()
        self.diversity_service = DiversityService()

        # Queries
        self.get_recommendations_query = GetRecommendationsQuery(
            user_repository,
            movie_repository,
            rating_repository,
            model_server,
            feature_store,
            self.strategy_service,
            self.diversity_service,
        )

        self.explain_query = ExplainRecommendationQuery(
            user_repository, movie_repository, rating_repository
        )

    async def get_recommendations(
        self, request: GetRecommendationsRequest
    ) -> RecommendationListDTO:
        """
        Gera recomendações para usuário.

        Pipeline completo:
        - Análise de perfil
        - Seleção de estratégia
        - Geração (ML)
        - Re-ranking (diversidade)
        - Explicações

        Args:
            request: request de recomendações

        Returns:
            RecommendationListDTO com recomendações

        Raises:
            ValueError: se usuário não existir
        """
        # Executa query (pipeline completo)
        result = await self.get_recommendations_query.execute(request)

        # Persiste recomendações (para analytics)
        await self._persist_recommendations(result)

        return result

    async def explain_recommendation(
        self, request: ExplainRecommendationRequest
    ) -> Optional[ExplanationDTO]:
        """
        Explica por que um filme foi recomendado.

        Args:
            request: request de explicação

        Returns:
            ExplanationDTO com explicação detalhada
        """
        return await self.explain_query.execute(request)

    async def get_popular_recommendations(self, limit: int = 10) -> List[dict]:
        """
        Recomendações populares (cold start).

        Usado quando não há usuário autenticado.

        Args:
            limit: número de recomendações

        Returns:
            Lista de filmes populares
        """
        movies = await self.movie_repository.find_popular(min_rating_count=100, limit=limit)

        return [
            {
                "movie_id": int(m.id),
                "title": m.title,
                "genres": m.genres,
                "avg_rating": m.avg_rating,
                "rating_count": m.rating_count,
                "rank": idx + 1,
            }
            for idx, m in enumerate(movies)
        ]

    async def get_trending_recommendations(self, limit: int = 10) -> List[dict]:
        """
        Recomendações em alta (trending).

        Baseado em atividade recente.

        Args:
            limit: número de recomendações

        Returns:
            Lista de filmes trending
        """
        # Busca ratings recentes (últimos 7 dias)
        recent_ratings = await self.rating_repository.find_recent_ratings(days=7, limit=1000)

        # Conta frequência de movies
        from collections import Counter

        movie_counts = Counter(int(r.movie_id) for r in recent_ratings)

        # Top movies
        top_movie_ids = [movie_id for movie_id, _ in movie_counts.most_common(limit)]

        # Busca detalhes
        result = []
        for idx, movie_id in enumerate(top_movie_ids):
            from ...domain.value_objects import MovieId

            movie = await self.movie_repository.find_by_id(MovieId(movie_id))
            if movie:
                result.append(
                    {
                        "movie_id": int(movie.id),
                        "title": movie.title,
                        "genres": movie.genres,
                        "avg_rating": movie.avg_rating,
                        "rating_count": movie.rating_count,
                        "recent_interactions": movie_counts[movie_id],
                        "rank": idx + 1,
                    }
                )

        return result

    async def invalidate_user_cache(self, user_id: int) -> None:
        """
        Invalida cache de recomendações de um usuário.

        Chama quando:
        - Usuário avalia filme
        - Perfil muda

        Args:
            user_id: ID do usuário
        """
        # Invalida no model server
        self.model_server.invalidate_user_cache(user_id)

        # Invalida no feature store
        self.feature_store.invalidate_user_cache(user_id)

    async def _persist_recommendations(self, result: RecommendationListDTO) -> None:
        """
        Persiste recomendações para analytics.

        Args:
            result: resultado da geração
        """
        from ...domain.entities import Recommendation, RecommendationSource
        from ...domain.value_objects import MovieId, RecommendationScore, Timestamp, UserId

        # Converte DTOs para entities
        recommendations = []

        for rec_dto in result.recommendations:
            rec = Recommendation(
                user_id=UserId(result.user_id),
                movie_id=MovieId(rec_dto.movie_id),
                score=RecommendationScore(rec_dto.score),
                source=RecommendationSource(rec_dto.source),
                timestamp=Timestamp.now(),
                rank=rec_dto.rank,
                metadata=rec_dto.metadata or {},
            )
            recommendations.append(rec)

        # Salva em batch (substitui antigas)
        await self.recommendation_repository.save_batch(UserId(result.user_id), recommendations)
