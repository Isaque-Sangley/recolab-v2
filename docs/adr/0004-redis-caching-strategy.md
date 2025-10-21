# ADR 0005: Estratégia de Cache com Redis para Performance

## Status

Aceito

## Contexto

O sistema de recomendação enfrenta desafios de performance em operações frequentes:

**Gargalos Identificados**:
1. **Geração de recomendações**: 300-500ms (ML model inference + database queries)
2. **Busca de filmes populares**: 100-150ms (agregação em milhões de ratings)
3. **Perfil de usuário**: 50-80ms (join user + ratings + movies)
4. **Metadados de filmes**: 20-30ms por filme (queries repetidas)

**Padrões de Acesso**:
- 70% das recomendações são para os mesmos 20% de usuários (power users)
- Filmes populares são consultados repetidamente (top 100 representam 40% dos acessos)
- Metadados de filmes raramente mudam (atualização: ~1x/semana)
- Recomendações têm validade temporal (válidas por 1-24h dependendo do usuário)

**Requisitos**:
- Reduzir latência P95 de 500ms para < 200ms
- Suportar 200+ req/s sem degradação
- Minimizar carga no PostgreSQL
- Invalidação inteligente de cache (usuário avalia filme → invalida recomendações)

## Decisão

Implementar estratégia de cache em três camadas usando Redis:

**Layer 1: Application-Level Cache (Redis)**

**Dados Cacheados**:
```python
# Recomendações de usuários
Key: "recommendations:user:{user_id}:n:{n}:strategy:{strategy}"
TTL: 1 hora (casual users), 24 horas (power users)
Payload: List[RecommendationDTO]

# Filmes populares
Key: "movies:popular:limit:{limit}"
TTL: 6 horas
Payload: List[MovieDTO]

# Perfil de usuário
Key: "user:profile:{user_id}"
TTL: 30 minutos
Payload: UserProfileDTO (inclui favorite_genres, statistics)

# Metadados de filme
Key: "movie:metadata:{movie_id}"
TTL: 24 horas
Payload: MovieDTO

# Model embeddings (otimização futura)
Key: "embeddings:user:{user_id}"
TTL: 7 dias
Payload: np.array (embedding vector)
```

**Layer 2: Query Result Cache (PostgreSQL)**

Para queries complexas que não mudam frequentemente:
```sql
-- Materializado: Filmes bem avaliados por gênero
CREATE MATERIALIZED VIEW top_movies_by_genre AS
SELECT genre, movie_id, avg_rating, rating_count
FROM movies_genres
WHERE rating_count > 50
ORDER BY genre, avg_rating DESC;

-- Refresh: 1x por hora via cron job
```

**Layer 3: HTTP Cache Headers**

Para conteúdo estático (posters, metadados públicos):
```python
@app.get("/movies/{movie_id}")
async def get_movie(movie_id: int):
    return Response(
        content=movie_data,
        headers={
            "Cache-Control": "public, max-age=3600",  # 1 hora
            "ETag": f'"{movie_id}-{movie.updated_at}"'
        }
    )
```

**Invalidação de Cache**:

**Event-Driven Invalidation**:
```python
# Quando usuário cria rating
@event_handler(RatingCreatedEvent)
async def invalidate_user_cache(event: RatingCreatedEvent):
    await redis.delete(f"recommendations:user:{event.user_id}:*")
    await redis.delete(f"user:profile:{event.user_id}")
    
    # Invalida cache de filme se estatísticas mudaram significativamente
    if event.is_milestone():  # e.g., 100º rating
        await redis.delete(f"movies:popular:*")
```

**Time-Based Invalidation**:
- TTLs ajustados por frequência de mudança
- Cache warming para dados críticos (top 100 movies pré-carregados)

## Consequências

### Positivas

1. **Performance Dramática**: Recomendações cacheadas servidas em < 10ms (vs 400ms sem cache).

2. **Redução de Carga DB**: 70% das queries evitadas. PostgreSQL connection pool não satura.

3. **Escalabilidade**: Redis suporta 100k+ ops/s. Bottleneck deixa de ser database.

4. **Resiliência**: Se PostgreSQL cair, cache permite operação degradada (stale data por alguns minutos).

5. **Cost Efficiency**: Redis managed (AWS ElastiCache) é mais barato que escalar PostgreSQL verticalmente.

6. **Flexibilidade**: TTLs configuráveis por tipo de dado permitem fine-tuning.

### Negativas

1. **Complexidade Operacional**: Mais um serviço para monitorar (Redis health, memory usage).

2. **Stale Data**: Usuário pode ver recomendações antigas por até 1h após avaliar filme.

3. **Cache Warming**: Cold start do Redis após restart causa spike de latência.

4. **Invalidação Difícil**: Invalidar cache relacionado requer lógica complexa (e.g., filmes similares ao que foi avaliado).

5. **Memory Management**: Redis precisa de eviction policy (allkeys-lru) para evitar OOM.

6. **Debugging**: Problemas intermitentes difíceis de reproduzir (funciona quando cache está quente).

## Alternativas Consideradas

### Memcached
**Rejeitado**:
- Não tem estruturas de dados avançadas (Redis tem Lists, Sets, Hashes)
- Não tem persistência (Redis tem RDB/AOF)
- Pior integração com Python (redis-py é superior a pylibmc)

**Casos onde seria melhor**: Cache simples key-value, quando persistência não importa

### Application-Level Cache (LRU Cache in-memory)
**Rejeitado**:
- Não compartilhado entre instâncias (problema com horizontal scaling)
- Perda de cache em cada deploy
- Memory limitada da aplicação

**Casos onde seria melhor**: Single-instance apps, caches pequenos (<100MB)

### Varnish (HTTP Cache)
**Considerado complementar**:
- Excelente para caching de HTML/JSON responses
- Não ajuda com lógica interna da aplicação
- Considerado para v2.0 como reverse proxy

### CDN (CloudFlare, Fastly)
**Fora de escopo**:
- Ótimo para assets estáticos (imagens, CSS, JS)
- Não ajuda com APIs dinâmicas
- Considerado para frontend em v2.0

### Database Query Cache (PostgreSQL)
**Insuficiente sozinho**:
- Ajuda mas não evita parsing/planning de queries
- Não ajuda com application-level computation (ML inference)
- Complementa mas não substitui Redis

## Implementação

**Redis Configuration**:
```python
# Dockerfile / docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  ports:
    - "6379:6379"
```

**Python Client**:
```python
from redis.asyncio import Redis
from typing import Optional, Any
import json

class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache, deserialize JSON"""
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: int = 3600
    ) -> None:
        """Serialize to JSON and cache"""
        await self.redis.setex(
            key,
            ttl_seconds,
            json.dumps(value, default=str)
        )
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0
```

**Cache Decorator**:
```python
def cached(
    key_prefix: str,
    ttl_seconds: int = 3600,
    key_builder: Callable = None
):
    """Decorator para cachear resultados de funções"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = key_builder(*args, **kwargs) if key_builder else f"{key_prefix}:{args}:{kwargs}"
            
            # Try cache
            cached_result = await cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator

# Usage
@cached(
    key_prefix="recommendations",
    ttl_seconds=3600,
    key_builder=lambda user_id, n: f"recommendations:user:{user_id}:n:{n}"
)
async def get_recommendations(user_id: int, n: int):
    # Expensive computation
    ...
```

## Monitoramento

**Métricas Redis**:
```python
# Via redis-py
info = await redis.info()
metrics = {
    "used_memory_mb": info["used_memory"] / 1024 / 1024,
    "hit_rate": info["keyspace_hits"] / (info["keyspace_hits"] + info["keyspace_misses"]),
    "evicted_keys": info["evicted_keys"],
    "connected_clients": info["connected_clients"],
    "ops_per_sec": info["instantaneous_ops_per_sec"]
}
```

**Target Metrics**:
- Hit rate > 70%
- Latência P95 Redis < 5ms
- Memory usage < 80% (eviction antes de OOM)
- Zero connection timeouts

**Alertas**:
- Hit rate < 60%: Cache warming inadequado ou TTLs muito curtos
- Memory > 90%: Aumentar maxmemory ou ajustar eviction
- Latência > 10ms: Redis sobrecarregado, considerar sharding

## Cache Warming Strategy
```python
async def warm_cache():
    """Pre-load critical data on startup"""
    # Top 100 popular movies
    popular_movies = await movie_repo.find_popular(limit=100)
    await cache.set("movies:popular:limit:100", popular_movies, ttl=21600)
    
    # Power users (top 20% by activity)
    power_users = await user_repo.find_power_users(limit=1000)
    for user in power_users:
        recommendations = await recommendation_service.generate(user.id)
        await cache.set(f"recommendations:user:{user.id}", recommendations, ttl=86400)
```

## Debugging & Troubleshooting

**Cache Hit Rate Baixo**:
1. Verificar TTLs (podem estar muito curtos)
2. Analisar distribution de keys (muitas variações → low reuse)
3. Revisar invalidation logic (invalidando muito frequentemente)

**Stale Data**:
1. Reduzir TTLs para dados críticos
2. Implementar event-driven invalidation
3. Adicionar timestamp ao payload para client-side validation

**OOM (Out of Memory)**:
1. Implementar eviction policy (allkeys-lru)
2. Aumentar maxmemory
3. Sharding se single instance não é suficiente

## Experimentos Futuros

1. **Redis Cluster**: Sharding para > 1M users
2. **Predictive Cache Warming**: ML para prever quais usuários vão fazer requests
3. **Cache Probability**: Cachear apenas items com alta probabilidade de reuso
4. **Multi-Region**: Redis replication para baixa latência global

## Referências

- Caching Strategies and Patterns: https://aws.amazon.com/pt/caching/best-practices/