"""
Load MovieLens Data Script

Carrega dados do MovieLens no banco de dados.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.database import get_session
from src.infrastructure.persistence.orm_models import MovieORM, RatingORM, UserORM


async def load_movies(data_path: Path, session):
    """Carrega filmes"""
    print("Carregando filmes...")

    movies_df = pd.read_csv(data_path / "movies.csv")

    movies_added = 0

    for _, row in movies_df.iterrows():
        # Extrai ano do título (formato: "Title (YYYY)")
        title = row["title"]
        year = None

        if "(" in title and ")" in title:
            try:
                year_str = title[title.rfind("(") + 1 : title.rfind(")")]
                if year_str.isdigit() and len(year_str) == 4:
                    year = int(year_str)
            except Exception:
                pass

        # Processa gêneros
        genres = []
        if row["genres"] != "(no genres listed)":
            genres = [g.strip() for g in row["genres"].split("|")]

        # Cria movie
        movie = MovieORM(
            id=int(row["movieId"]),
            title=title,
            genres=genres,
            year=year,
            rating_count=0,
            avg_rating=0.0,
        )

        session.add(movie)
        movies_added += 1

        if movies_added % 1000 == 0:
            await session.flush()
            print(f"   {movies_added} filmes processados...")

    await session.commit()
    print(f"{movies_added} filmes carregados!")

    return movies_added


async def load_ratings(data_path: Path, session, sample_size: int = None):
    """Carrega ratings"""
    print("Carregando ratings...")

    ratings_df = pd.read_csv(data_path / "ratings.csv")

    # Sample se especificado
    if sample_size and len(ratings_df) > sample_size:
        print(f"   Usando sample de {sample_size} ratings (de {len(ratings_df)})")
        ratings_df = ratings_df.sample(n=sample_size, random_state=42)

    # Pré-cria usuários únicos
    unique_users = ratings_df["userId"].unique()
    print(f"   Criando {len(unique_users)} usuários...")

    for user_id in unique_users:
        user = UserORM(
            id=int(user_id),
            created_at=datetime.now(),
            n_ratings=0,
            avg_rating=0.0,
            favorite_genres=[],
            last_activity=None,
        )
        session.add(user)

    await session.flush()
    print(f"Usuários criados!")

    # Carrega ratings
    ratings_added = 0

    for _, row in ratings_df.iterrows():
        rating = RatingORM(
            user_id=int(row["userId"]),
            movie_id=int(row["movieId"]),
            score=float(row["rating"]),
            timestamp=pd.to_datetime(row["timestamp"], unit="s"),
        )

        session.add(rating)
        ratings_added += 1

        if ratings_added % 5000 == 0:
            await session.flush()
            print(f"   {ratings_added} ratings processados...")

    await session.commit()
    print(f"{ratings_added} ratings carregados!")

    return ratings_added


async def update_statistics(session):
    """Atualiza estatísticas agregadas"""
    print("Calculando estatísticas...")

    from sqlalchemy import text

    # Atualiza movie statistics
    await session.execute(
        text(
            """
        UPDATE movies m
        SET 
            rating_count = COALESCE(r.count, 0),
            avg_rating = COALESCE(r.avg, 0.0)
        FROM (
            SELECT 
                movie_id,
                COUNT(*) as count,
                AVG(score) as avg
            FROM ratings
            GROUP BY movie_id
        ) r
        WHERE m.id = r.movie_id
    """
        )
    )

    # Atualiza user statistics
    await session.execute(
        text(
            """
        UPDATE users u
        SET 
            n_ratings = COALESCE(r.count, 0),
            avg_rating = COALESCE(r.avg, 0.0),
            last_activity = COALESCE(r.last_ts, u.created_at)
        FROM (
            SELECT 
                user_id,
                COUNT(*) as count,
                AVG(score) as avg,
                MAX(timestamp) as last_ts
            FROM ratings
            GROUP BY user_id
        ) r
        WHERE u.id = r.user_id
    """
        )
    )

    await session.commit()
    print("Estatísticas atualizadas!")


async def calculate_favorite_genres(session):
    """Calcula gêneros favoritos dos usuários"""
    print("Calculando gêneros favoritos...")

    from collections import Counter

    from sqlalchemy import select

    # Busca todos os usuários
    result = await session.execute(select(UserORM))
    users = result.scalars().all()

    updated = 0

    for user in users:
        # Busca ratings do usuário (4+ estrelas)
        result = await session.execute(
            select(RatingORM).where(RatingORM.user_id == user.id).where(RatingORM.score >= 4.0)
        )
        high_ratings = result.scalars().all()

        if not high_ratings:
            continue

        # Busca filmes desses ratings
        movie_ids = [r.movie_id for r in high_ratings]
        result = await session.execute(select(MovieORM).where(MovieORM.id.in_(movie_ids)))
        movies = result.scalars().all()

        # Conta gêneros
        genre_counter = Counter()
        for movie in movies:
            for genre in movie.genres:
                genre_counter[genre] += 1

        # Top 3 gêneros
        top_genres = [genre for genre, _ in genre_counter.most_common(3)]

        user.favorite_genres = top_genres
        updated += 1

        if updated % 100 == 0:
            await session.flush()
            print(f"   {updated} usuários processados...")

    await session.commit()
    print(f"Gêneros favoritos calculados para {updated} usuários!")


async def main():
    """Main function"""
    print("=" * 60)
    print("  RECOLAB - LOAD MOVIELENS DATA")
    print("=" * 60)
    print()

    # Verifica se dados existem
    data_path = Path("data/ml-latest-small")

    if not data_path.exists():
        print("Dados não encontrados!")
        print("\n Baixe o MovieLens dataset:")
        print("   mkdir -p data")
        print("   cd data")
        print("   wget https://files.grouplens.org/datasets/movielens/ml-latest-small.zip")
        print("   unzip ml-latest-small.zip")
        print("   cd ..")
        sys.exit(1)

    print(f"Dados encontrados em: {data_path}")
    print()

    # Pergunta sobre sample
    print("Opções de carga:")
    print("  1. Full dataset (~100k ratings)")
    print("  2. Sample de 10k ratings (recomendado para testes)")
    print("  3. Sample de 50k ratings")

    choice = input("\nEscolha (1/2/3) [2]: ").strip() or "2"

    sample_sizes = {"1": None, "2": 10000, "3": 50000}

    sample_size = sample_sizes.get(choice, 10000)

    print()
    print("Iniciando carga de dados...")
    print()

    async for session in get_session():
        try:
            # Carrega filmes
            await load_movies(data_path, session)
            print()

            # Carrega ratings
            await load_ratings(data_path, session, sample_size)
            print()

            # Atualiza estatísticas
            await update_statistics(session)
            print()

            # Calcula gêneros favoritos
            await calculate_favorite_genres(session)
            print()

            print("=" * 60)
            print("  DADOS CARREGADOS COM SUCESSO!")
            print("=" * 60)

            break

        except Exception as e:
            print(f"\n Erro: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
