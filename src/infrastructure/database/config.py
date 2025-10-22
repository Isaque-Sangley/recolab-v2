"""
Database Configuration

Configuração do SQLAlchemy (async) para PostgreSQL.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


class DatabaseConfig:
    """
    Database configuration singleton.

    Gerencia engine e sessions do SQLAlchemy.
    """

    def __init__(self, database_url: str, echo: bool = False):
        """
        Args:
            database_url: Database URL (postgresql+asyncpg://...)
            echo: Se True, loga SQL queries
        """
        self.database_url = database_url
        self.echo = echo

        # Cria async engine
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=NullPool,  # Desabilita pool para simplificar
            future=True,
        )

        # Session factory
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Retorna session do banco.

        Usage:
            async for session in db_config.get_session():
                # use session
                pass
        """
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """
        Cria todas as tabelas no banco.

        ATENÇÃO: Em produção, use migrations (Alembic).
        """
        from .models import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Database tables created")

    async def drop_tables(self):
        """
        Remove todas as tabelas (CUIDADO! Apenas dev).
        """
        from .models import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        print("🗑️  Database tables dropped")

    async def close(self):
        """Fecha conexões do banco"""
        await self.engine.dispose()


# Singleton instance
_db_config: DatabaseConfig = None


def get_database_config(database_url: str = None, echo: bool = False) -> DatabaseConfig:
    """
    Retorna configuração do banco (singleton).

    Args:
        database_url: Database URL (se None, usa .env)
        echo: Se True, loga SQL queries

    Returns:
        DatabaseConfig instance
    """
    global _db_config

    if _db_config is None:
        # Carrega URL do .env se não fornecida
        if database_url is None:
            import os
            from pathlib import Path

            from dotenv import load_dotenv

            # Carrega .env
            env_path = Path(__file__).parent.parent.parent.parent / ".env"
            load_dotenv(env_path)

            database_url = os.getenv(
                "DATABASE_URL", "postgresql+asyncpg://recolab:recolab123@localhost:5432/recolab"
            )

            echo_env = os.getenv("SQL_ECHO", "False")
            echo = echo_env.lower() == "true"

        _db_config = DatabaseConfig(database_url, echo)

    return _db_config


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obter session do banco.

    Usage:
        async for session in get_session():
            # use session
            pass
    """
    db_config = get_database_config()
    async for session in db_config.get_session():
        yield session
