# ADR 0004: Sistema de Recomendação Multi-Stage Adaptativo

## Status

Aceito

## Contexto

Diferentes usuários têm perfis de interação distintos que requerem estratégias de recomendação diferenciadas:

**Cold Start Users** (0 ratings)
- Sem histórico para collaborative filtering
- Alta taxa de churn se receberem recomendações ruins
- Precisam de onboarding eficaz

**New Users** (1-5 ratings)
- Histórico insuficiente para CF confiável
- Preferences ainda sendo descobertas

**Casual Users** (6-20 ratings)
- Perfil emergente mas ainda volátil
- Collaborative filtering começa a ser eficaz

**Active Users** (21-100 ratings)
- Perfil estável e confiável
- CF produz melhores resultados

**Power Users** (100+ ratings)
- Alto engajamento
- Risco de filter bubble (sempre os mesmos gêneros)
- Precisam de diversidade e serendipity

Uma única estratégia para todos os perfis resulta em:
- Cold start users recebem recomendações genéricas
- Power users caem em echo chambers
- Métricas globais mascaradas (80% dos usuários são cold start)

## Decisão

Implementar sistema multi-stage adaptativo que seleciona estratégia baseada no perfil do usuário:

**Stage 1: User Classification**
```python
class UserClassification(Enum):
    COLD_START = "cold_start"      # 0 ratings
    NEW = "new"                     # 1-5 ratings
    CASUAL = "casual"               # 6-20 ratings
    ACTIVE = "active"               # 21-100 ratings
    POWER_USER = "power_user"       # 100+ ratings
```

**Stage 2: Strategy Selection**

| User Type | Primary Strategy | Fallback | Weight Distribution |
|-----------|-----------------|----------|---------------------|
| Cold Start | Popular | Content-Based | 100% Popular |
| New | Content-Based | Popular | 70% CB + 30% Pop |
| Casual | Hybrid | Content-Based | 60% CF + 40% CB |
| Active | Collaborative | Hybrid | 80% CF + 20% CB |
| Power User | Collaborative | + Diversity | 70% CF + 30% Serendipity |

**Stage 3: Diversity Optimization**

Para Power Users, aplica-se re-ranking MMR (Maximal Marginal Relevance):
```
score(item) = λ * relevance(item) - (1-λ) * max_similarity(item, selected_items)
```
onde λ = 0.7 (balanceia relevância vs diversidade)

**Stage 4: Post-Processing**
- Filtra filmes já avaliados
- Remove duplicatas
- Ordena por score final
- Limita a N resultados

## Consequências

### Positivas

1. **Personalização por Segmento**: Cada tipo de usuário recebe estratégia otimizada.

2. **Cold Start Resolvido**: Novos usuários recebem filmes populares de alta qualidade (avg rating > 4.0).

3. **Evita Filter Bubble**: Power users recebem diversidade via MMR, descobrem novos gêneros.

4. **Métricas Segmentadas**: Podemos otimizar separadamente para cada cohort.

5. **Graceful Degradation**: Se CF falhar, fallback para Content-Based é automático.

6. **Explicabilidade**: Usuário sabe que cold start recebe "populares" e power users "baseado em seu histórico".

### Negativas

1. **Complexidade de Código**: Múltiplas estratégias requerem mais testes e manutenção.

2. **Tuning de Hiperparâmetros**: Thresholds (5, 20, 100 ratings) foram escolhidos empiricamente, podem não ser ótimos.

3. **Inconsistência Temporal**: Usuário pode receber recomendações muito diferentes ao cruzar threshold (20→21 ratings).

4. **Custo Computacional**: Calcular múltiplas estratégias aumenta latência (mitigado com cache).

## Alternativas Consideradas

### Estratégia Única (Collaborative Filtering)
**Rejeitado**:
- Completamente ineficaz para cold start
- 60% dos usuários em sistemas reais são cold start
- Churn rate alto para novos usuários

### Bandit Algorithms (Multi-Armed Bandit)
**Considerado para v2.0**:
- Excelente para exploration/exploitation
- Requer infraestrutura de logging e feedback loop
- Complexidade prematura para MVP
- Implementação futura com Thompson Sampling

### Context-Aware Recommendations
**Considerado para v2.0**:
- Adicionar features contextuais (hora do dia, dispositivo, localização)
- Requer coleta de dados adicionais
- Privacy concerns (LGPD/GDPR)

### Deep Reinforcement Learning
**Rejeitado**:
- Estado da arte em YouTube/Netflix
- Requer simulador de ambiente ou logs históricos massivos
- Complexidade de implementação extrema
- Não justificado para escala do MVP

### Rule-Based System
**Rejeitado**:
- Simples de implementar mas não escala
- Regras manuais ficam desatualizadas rapidamente
- Sem aprendizado automático

## Implementação

**Domain Service**:
```python
class RecommendationStrategyService:
    def select_strategy(self, user: User) -> RecommendationStrategy:
        classification = user.classify()
        
        if classification == UserClassification.COLD_START:
            return PopularStrategy(min_rating_count=50, min_avg_rating=4.0)
        
        elif classification == UserClassification.NEW:
            return HybridStrategy(
                content_based_weight=0.7,
                popular_weight=0.3,
                user_favorite_genres=[]
            )
        
        elif classification == UserClassification.CASUAL:
            return HybridStrategy(
                collaborative_weight=0.6,
                content_based_weight=0.4,
                user_favorite_genres=user.favorite_genres
            )
        
        elif classification == UserClassification.ACTIVE:
            return HybridStrategy(
                collaborative_weight=0.8,
                content_based_weight=0.2,
                user_favorite_genres=user.favorite_genres
            )
        
        else:  # POWER_USER
            return MultiStageStrategy(
                primary=CollaborativeStrategy(),
                diversity_optimization=True,
                diversity_weight=0.3,
                serendipity_boost=0.2
            )
```

**Diversity Re-ranking**:
```python
class DiversityService:
    def rerank_for_diversity(
        self,
        recommendations: List[Recommendation],
        movies: List[Movie],
        lambda_param: float = 0.7
    ) -> List[Recommendation]:
        """
        MMR (Maximal Marginal Relevance) algorithm
        """
        selected = []
        remaining = list(recommendations)
        
        # Primeiro item = mais relevante
        selected.append(remaining.pop(0))
        
        while remaining and len(selected) < desired_count:
            best_score = -float('inf')
            best_idx = 0
            
            for idx, rec in enumerate(remaining):
                movie = movies[rec.movie_id]
                
                # Relevância original
                relevance = rec.score
                
                # Similaridade máxima com já selecionados
                max_sim = max(
                    movie.genre_similarity(selected_movie)
                    for selected_movie in selected
                )
                
                # MMR score
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                
                if mmr > best_score:
                    best_score = mmr
                    best_idx = idx
            
            selected.append(remaining.pop(best_idx))
        
        return selected
```

## Métricas de Sucesso

**Por Segmento**:
- Cold Start: Click-through rate > 15%
- New Users: Return rate (7 days) > 40%
- Casual: Average rating of recommendations > 3.8
- Active: Precision@10 > 0.3
- Power Users: Diversity score > 0.7, Serendipity > 0.2

**Global**:
- Latência P95 < 500ms
- Coverage (% filmes recomendados) > 60%
- No filter bubble: Gini coefficient < 0.6

## Monitoramento
```python
# Logs estruturados
{
    "user_id": 123,
    "user_classification": "active",
    "strategy_used": "hybrid",
    "weights": {"cf": 0.8, "cb": 0.2},
    "latency_ms": 234,
    "n_recommendations": 10,
    "diversity_score": 0.65
}
```

**Dashboards**:
- Distribuição de usuários por classificação
- Strategy selection breakdown
- Latência por estratégia
- Click-through rate por segmento


## Referências

- Netflix Recommendations: Beyond the 5 stars