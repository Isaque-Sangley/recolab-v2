"""
User Repository Implementation (PostgreSQL)

Implementação concreta do IUserRepository usando SQLAlchemy.
"""

from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories import IUserRepository
from ...domain.entities import User
from ...domain.value_objects import UserId
from ..database.models import UserModel
from ..database.mappers import UserMapper


class UserRepository(IUserRepository):
    """
    Implementação PostgreSQL do IUserRepository.
    
    Responsabilidades:
    - Traduzir operações de domínio para SQL
    - Usar mappers para conversão Domain ↔ ORM
    - Gerenciar transações
    """
    
    def __init__(self, session: AsyncSession):
        """
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.mapper = UserMapper()
    
    async def save(self, entity: User) -> User:
        """
        Salva ou atualiza usuário.
        
        Lógica:
        - Se existe, atualiza
        - Se não existe, cria novo
        """
        # Verifica se já existe
        stmt = select(UserModel).where(UserModel.id == int(entity.id))
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Atualiza existente
            self.mapper.update_model(existing, entity)
            await self.session.flush()
            return self.mapper.to_domain(existing)
        else:
            # Cria novo
            model = self.mapper.to_model(entity)
            self.session.add(model)
            await self.session.flush()
            return self.mapper.to_domain(model)
    
    async def find_by_id(self, entity_id: UserId) -> Optional[User]:
        """Busca usuário por ID"""
        stmt = select(UserModel).where(UserModel.id == int(entity_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self.mapper.to_domain(model) if model else None
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Lista todos os usuários (paginado)"""
        stmt = (
            select(UserModel)
            .order_by(UserModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def delete(self, entity_id: UserId) -> bool:
        """Remove usuário"""
        stmt = select(UserModel).where(UserModel.id == int(entity_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        
        return False
    
    async def exists(self, entity_id: UserId) -> bool:
        """Verifica se usuário existe"""
        stmt = select(func.count()).select_from(UserModel).where(UserModel.id == int(entity_id))
        result = await self.session.execute(stmt)
        count = result.scalar()
        
        return count > 0
    
    async def count(self) -> int:
        """Conta total de usuários"""
        stmt = select(func.count()).select_from(UserModel)
        result = await self.session.execute(stmt)
        return result.scalar()
    
    # Métodos específicos do IUserRepository
    
    async def find_by_type(self, user_type: str, limit: int = 100) -> List[User]:
        """
        Busca usuários por tipo.
        
        Implementação:
        - Mapeia user_type para range de n_ratings
        - Executa query filtrada
        """
        # Mapeia tipo para range
        type_ranges = {
            "cold_start": (0, 0),
            "new": (1, 4),
            "casual": (5, 19),
            "active": (20, 99),
            "power_user": (100, 999999)
        }
        
        if user_type not in type_ranges:
            return []
        
        min_ratings, max_ratings = type_ranges[user_type]
        
        stmt = (
            select(UserModel)
            .where(
                and_(
                    UserModel.n_ratings >= min_ratings,
                    UserModel.n_ratings <= max_ratings
                )
            )
            .order_by(UserModel.n_ratings.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_active_users(self, days: int = 30, limit: int = 100) -> List[User]:
        """
        Busca usuários ativos (com atividade recente).
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stmt = (
            select(UserModel)
            .where(UserModel.last_activity >= cutoff_date)
            .order_by(UserModel.last_activity.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_by_favorite_genre(self, genre: str, limit: int = 100) -> List[User]:
        """
        Busca usuários que têm determinado gênero como favorito.
        
        Usa PostgreSQL array contains operator.
        """
        stmt = (
            select(UserModel)
            .where(UserModel.favorite_genres.contains([genre]))
            .order_by(UserModel.n_ratings.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_with_min_ratings(self, min_ratings: int, limit: int = 100) -> List[User]:
        """Busca usuários com pelo menos N ratings"""
        stmt = (
            select(UserModel)
            .where(UserModel.n_ratings >= min_ratings)
            .order_by(UserModel.n_ratings.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def get_user_stats(self) -> dict:
        """
        Retorna estatísticas gerais de usuários.
        
        Usa agregações SQL para performance.
        """
        # Total de usuários
        total_stmt = select(func.count()).select_from(UserModel)
        total_result = await self.session.execute(total_stmt)
        total_users = total_result.scalar()
        
        # Média de ratings por usuário
        avg_stmt = select(func.avg(UserModel.n_ratings))
        avg_result = await self.session.execute(avg_stmt)
        avg_ratings = avg_result.scalar() or 0.0
        
        # Usuários ativos (últimos 30 dias)
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=30)
        
        active_stmt = select(func.count()).select_from(UserModel).where(
            UserModel.last_activity >= cutoff
        )
        active_result = await self.session.execute(active_stmt)
        active_users = active_result.scalar()
        
        # Usuários por tipo (agregação)
        type_ranges = {
            "cold_start": (0, 0),
            "new": (1, 4),
            "casual": (5, 19),
            "active": (20, 99),
            "power_user": (100, 999999)
        }
        
        users_by_type = {}
        for user_type, (min_r, max_r) in type_ranges.items():
            type_stmt = select(func.count()).select_from(UserModel).where(
                and_(
                    UserModel.n_ratings >= min_r,
                    UserModel.n_ratings <= max_r
                )
            )
            type_result = await self.session.execute(type_stmt)
            users_by_type[user_type] = type_result.scalar()
        
        return {
            "total_users": total_users,
            "users_by_type": users_by_type,
            "avg_ratings_per_user": round(float(avg_ratings), 2),
            "active_users_last_30_days": active_users
        }
    
    async def bulk_save(self, users: List[User]) -> List[User]:
        """
        Salva múltiplos usuários de uma vez.
        
        Otimização: bulk insert/update.
        """
        saved_users = []
        
        for user in users:
            saved = await self.save(user)
            saved_users.append(saved)
        
        # Flush uma vez no final
        await self.session.flush()
        
        return saved_users