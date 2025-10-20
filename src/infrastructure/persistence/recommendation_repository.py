"""
Recommendation Repository Implementation (PostgreSQL)
"""

from typing import List, Optional
from sqlalchemy import select, func, and_, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories import IRecommendationRepository
from ...domain.entities import Recommendation, RecommendationSource
from ...domain.value_objects import UserId, MovieId
from ..database.models import RecommendationModel
from ..database.mappers import RecommendationMapper


class RecommendationRepository(IRecommendationRepository):
    """
    Implementação PostgreSQL do IRecommendationRepository.
    
    Estratégia de armazenamento:
    - Recomendações são efêmeras (cache)
    - Armazena última geração por usuário
    - Útil para analytics e debugging
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = RecommendationMapper()
    
    async def save(self, entity: Recommendation) -> Recommendation:
        """
        Salva recomendação.
        
        ID é gerado automaticamente pelo banco (autoincrement).
        """
        # Cria modelo SEM passar ID - deixa o banco gerar
        model = RecommendationModel(
            user_id=int(entity.user_id),
            movie_id=int(entity.movie_id),
            score=float(entity.score),
            source=entity.source.value,
            rank=entity.rank,
            timestamp=entity.timestamp.value,
            recommendation_metadata=entity.metadata
        )
        
        self.session.add(model)
        await self.session.flush()
        
        return self.mapper.to_domain(model)
    
    async def find_by_id(self, entity_id: int) -> Optional[Recommendation]:
        """Busca recomendação por ID"""
        stmt = select(RecommendationModel).where(RecommendationModel.id == entity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self.mapper.to_domain(model) if model else None
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Recommendation]:
        """Lista todas as recomendações (paginado)"""
        stmt = (
            select(RecommendationModel)
            .order_by(RecommendationModel.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def delete(self, entity_id: int) -> bool:
        """Remove recomendação"""
        stmt = select(RecommendationModel).where(RecommendationModel.id == entity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        
        return False
    
    async def exists(self, entity_id: int) -> bool:
        """Verifica se recomendação existe"""
        stmt = select(func.count()).select_from(RecommendationModel).where(
            RecommendationModel.id == entity_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0
    
    async def count(self) -> int:
        """Conta total de recomendações"""
        stmt = select(func.count()).select_from(RecommendationModel)
        result = await self.session.execute(stmt)
        return result.scalar()
    
    # Métodos específicos do IRecommendationRepository
    
    async def find_by_user(self, user_id: UserId, limit: int = 100) -> List[Recommendation]:
        """Busca recomendações de um usuário"""
        stmt = (
            select(RecommendationModel)
            .where(RecommendationModel.user_id == int(user_id))
            .order_by(RecommendationModel.timestamp.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_latest_by_user(self, user_id: UserId, n: int = 10) -> List[Recommendation]:
        """Busca últimas N recomendações de um usuário"""
        stmt = (
            select(RecommendationModel)
            .where(RecommendationModel.user_id == int(user_id))
            .order_by(
                RecommendationModel.timestamp.desc(),
                RecommendationModel.rank.asc()
            )
            .limit(n)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_by_source(self, source: RecommendationSource, limit: int = 100) -> List[Recommendation]:
        """Busca recomendações por source"""
        stmt = (
            select(RecommendationModel)
            .where(RecommendationModel.source == source.value)
            .order_by(RecommendationModel.timestamp.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def find_high_confidence(self, threshold: float = 0.7, limit: int = 100) -> List[Recommendation]:
        """Busca recomendações de alta confiança"""
        stmt = (
            select(RecommendationModel)
            .where(RecommendationModel.score >= threshold)
            .order_by(RecommendationModel.score.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(m) for m in models]
    
    async def delete_by_user(self, user_id: UserId) -> int:
        """Remove todas as recomendações de um usuário"""
        stmt = sql_delete(RecommendationModel).where(
            RecommendationModel.user_id == int(user_id)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        return result.rowcount
    
    async def save_batch(self, user_id: UserId, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Salva batch de recomendações"""
        # Remove antigas
        await self.delete_by_user(user_id)
        
        # Insere novas
        saved = []
        for rec in recommendations:
            saved_rec = await self.save(rec)
            saved.append(saved_rec)
        
        return saved
    
    async def get_recommendation_stats(self) -> dict:
        """Retorna estatísticas de recomendações"""
        # Total
        total_stmt = select(func.count()).select_from(RecommendationModel)
        total_result = await self.session.execute(total_stmt)
        total_recommendations = total_result.scalar()
        
        # Por fonte
        recommendations_by_source = {}
        for source in RecommendationSource:
            source_stmt = select(func.count()).select_from(RecommendationModel).where(
                RecommendationModel.source == source.value
            )
            source_result = await self.session.execute(source_stmt)
            recommendations_by_source[source.value] = source_result.scalar()
        
        # Score médio por fonte
        avg_score_by_source = {}
        for source in RecommendationSource:
            avg_stmt = select(func.avg(RecommendationModel.score)).where(
                RecommendationModel.source == source.value
            )
            avg_result = await self.session.execute(avg_stmt)
            avg_score = avg_result.scalar()
            avg_score_by_source[source.value] = round(float(avg_score), 3) if avg_score else 0.0
        
        # Alta confiança
        high_conf_stmt = select(func.count()).select_from(RecommendationModel).where(
            RecommendationModel.score >= 0.7
        )
        high_conf_result = await self.session.execute(high_conf_stmt)
        high_confidence_count = high_conf_result.scalar()
        
        high_confidence_percentage = (
            (high_confidence_count / total_recommendations * 100)
            if total_recommendations > 0 else 0.0
        )
        
        return {
            "total_recommendations": total_recommendations,
            "recommendations_by_source": recommendations_by_source,
            "avg_score_by_source": avg_score_by_source,
            "high_confidence_percentage": round(high_confidence_percentage, 2)
        }