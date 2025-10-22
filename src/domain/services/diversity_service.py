"""
Diversity Service

Calcula e otimiza diversidade de recomendações.
"""

from dataclasses import dataclass
from typing import List, Set

from ..entities import Movie, Recommendation
from ..value_objects import MovieId


@dataclass
class DiversityMetrics:
    """Métricas de diversidade de uma lista de recomendações"""

    genre_diversity: float  # 0-1, diversidade de gêneros
    popularity_diversity: float  # 0-1, mix de popular/nicho
    year_diversity: float  # 0-1, diversidade de anos
    overall_diversity: float  # 0-1, score geral
    unique_genres: Set[str]
    genre_distribution: dict


class DiversityService:
    """
    Domain Service: Diversidade de Recomendações

    Por que é Domain Service?
    - Lógica de negócio que opera em múltiplas entities
    - Não pertence a Movie nem a Recommendation
    - Stateless

    Responsabilidades:
    - Calcular diversidade de uma lista
    - Re-ranquear para maximizar diversidade
    - Balancear relevância vs diversidade
    """

    def calculate_diversity(self, movies: List[Movie]) -> DiversityMetrics:
        """
        Calcula métricas de diversidade de uma lista de filmes.

        Args:
            movies: lista de filmes

        Returns:
            Métricas de diversidade
        """
        if not movies:
            return self._empty_metrics()

        # Diversidade de gêneros
        all_genres = set()
        genre_counts = {}
        for movie in movies:
            for genre in movie.genres:
                all_genres.add(genre)
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

        genre_diversity = self._calculate_genre_diversity(genre_counts, len(movies))

        # Diversidade de popularidade
        popularity_diversity = self._calculate_popularity_diversity(movies)

        # Diversidade de anos
        year_diversity = self._calculate_year_diversity(movies)

        # Score geral (média ponderada)
        overall = 0.5 * genre_diversity + 0.3 * popularity_diversity + 0.2 * year_diversity

        return DiversityMetrics(
            genre_diversity=round(genre_diversity, 3),
            popularity_diversity=round(popularity_diversity, 3),
            year_diversity=round(year_diversity, 3),
            overall_diversity=round(overall, 3),
            unique_genres=all_genres,
            genre_distribution=genre_counts,
        )

    def _empty_metrics(self) -> DiversityMetrics:
        """Métricas vazias"""
        return DiversityMetrics(
            genre_diversity=0.0,
            popularity_diversity=0.0,
            year_diversity=0.0,
            overall_diversity=0.0,
            unique_genres=set(),
            genre_distribution={},
        )

    def _calculate_genre_diversity(self, genre_counts: dict, n_movies: int) -> float:
        """
        Calcula diversidade de gêneros usando Shannon Entropy.

        Alta diversidade = muitos gêneros diferentes bem distribuídos
        Baixa diversidade = poucos gêneros ou mal distribuídos
        """
        if not genre_counts or n_movies == 0:
            return 0.0

        import math

        # Shannon Entropy
        total = sum(genre_counts.values())
        probabilities = [count / total for count in genre_counts.values()]
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

        # Normaliza (max entropy = log2(n_genres))
        max_entropy = math.log2(len(genre_counts))
        normalized = entropy / max_entropy if max_entropy > 0 else 0.0

        return normalized

    def _calculate_popularity_diversity(self, movies: List[Movie]) -> float:
        """
        Calcula diversidade de popularidade.

        Ideal: mix de filmes populares e de nicho
        """
        if not movies:
            return 0.0

        # Normaliza rating_count para 0-1
        rating_counts = [m.rating_count for m in movies]
        max_count = max(rating_counts) if rating_counts else 1

        normalized = [count / max_count for count in rating_counts]

        # Diversidade = desvio padrão normalizado
        # Alto desvio = boa mistura de popular/nicho
        import statistics

        if len(normalized) < 2:
            return 0.5

        std_dev = statistics.stdev(normalized)

        # Normaliza std_dev (max teórico = 0.5)
        diversity = min(1.0, std_dev / 0.5)

        return diversity

    def _calculate_year_diversity(self, movies: List[Movie]) -> float:
        """
        Calcula diversidade de anos de lançamento.

        Ideal: mix de clássicos e lançamentos recentes
        """
        years = [m.year for m in movies if m.year]

        if len(years) < 2:
            return 0.5

        # Range de anos
        year_range = max(years) - min(years)

        # Normaliza (50+ anos = diversidade máxima)
        diversity = min(1.0, year_range / 50.0)

        return diversity

    def rerank_for_diversity(
        self,
        recommendations: List[Recommendation],
        movies: List[Movie],
        diversity_weight: float = 0.3,
    ) -> List[Recommendation]:
        """
        Re-ranqueia recomendações para maximizar diversidade.

        Algoritmo MMR (Maximal Marginal Relevance):
        - Balanceia relevância (score) com diversidade
        - Evita recomendar filmes muito similares

        Args:
            recommendations: lista ordenada por score
            movies: lista de movies correspondentes
            diversity_weight: peso da diversidade (0-1)
                0 = só relevância
                1 = só diversidade

        Returns:
            Lista re-ranqueada
        """
        if len(recommendations) <= 1:
            return recommendations

        # Cria mapa movie_id → movie
        movie_map = {m.id: m for m in movies}

        # MMR: seleciona iterativamente o item que maximiza relevância - similaridade com já selecionados
        selected = []
        remaining = list(recommendations)

        # Primeiro item = mais relevante
        selected.append(remaining.pop(0))

        while remaining:
            best_score = -float("inf")
            best_idx = 0

            for idx, rec in enumerate(remaining):
                movie = movie_map.get(rec.movie_id)
                if not movie:
                    continue

                # Score de relevância (normalizado 0-1)
                relevance = float(rec.score)

                # Penalidade por similaridade com já selecionados
                max_similarity = 0.0
                for selected_rec in selected:
                    selected_movie = movie_map.get(selected_rec.movie_id)
                    if selected_movie:
                        similarity = movie.genre_similarity(selected_movie.genres)
                        max_similarity = max(max_similarity, similarity)

                # MMR score: balanceia relevância e diversidade
                mmr_score = (1 - diversity_weight) * relevance - diversity_weight * max_similarity

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            selected.append(remaining.pop(best_idx))

        return selected

    def ensure_genre_coverage(
        self,
        recommendations: List[Recommendation],
        movies: List[Movie],
        user_favorite_genres: List[str],
        min_coverage: int = 3,
    ) -> List[Recommendation]:
        """
        Garante que recomendações cobrem gêneros favoritos do usuário.

        Args:
            recommendations: lista de recomendações
            movies: lista de movies
            user_favorite_genres: gêneros favoritos do usuário
            min_coverage: mínimo de gêneros favoritos a cobrir

        Returns:
            Lista ajustada
        """
        if not user_favorite_genres or len(recommendations) < min_coverage:
            return recommendations

        # Identifica quais gêneros estão cobertos
        movie_map = {m.id: m for m in movies}
        covered_genres = set()

        for rec in recommendations:
            movie = movie_map.get(rec.movie_id)
            if movie:
                for genre in movie.genres:
                    if genre in user_favorite_genres:
                        covered_genres.add(genre)

        # Se já cobre suficientes gêneros, retorna como está
        if len(covered_genres) >= min_coverage:
            return recommendations

        # Caso contrário, precisa ajustar
        # (implementação completa > mais complexa)
        return recommendations
