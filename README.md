<div align="center">

# 🎬 RecoLab v2

### Sistema Avançado de Recomendação de Filmes com Deep Learning

[![CI Pipeline](https://github.com/Isaque-Sangley/recolab-v2/actions/workflows/ci.yml/badge.svg)](https://github.com/Isaque-Sangley/recolab-v2/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/SEU_USERNAME/recolab-v2/branch/main/graph/badge.svg)](https://codecov.io/gh/SEU_USERNAME/recolab-v2)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Docs](#-api-documentation) • [Tech Stack](#-tech-stack)

</div>

---

## 🎯 **Sobre o Projeto**

**RecoLab v2** é um sistema de recomendação de filmes de nível **production-ready** que combina múltiplas técnicas de Machine Learning para gerar recomendações personalizadas e precisas.

O projeto demonstra expertise em:
- 🏗️ **Clean Architecture** (DDD) com separação clara de responsabilidades
- 🤖 **Deep Learning** com Neural Collaborative Filtering (PyTorch)
- 🔄 **Sistemas Híbridos** (Collaborative + Content-Based + Popular)
- ⚡ **APIs de Alta Performance** (FastAPI + PostgreSQL + Redis)
- 🧪 **Testes Abrangentes** (140+ testes, 85%+ coverage)
- 🚀 **CI/CD Pipeline** completo com GitHub Actions

---

## ✨ **Features**

### 🎯 **Recomendações Inteligentes**
- **Adaptive Strategy**: Sistema escolhe automaticamente a melhor estratégia baseado no perfil do usuário
- **Neural Collaborative Filtering**: Deep Learning para capturar padrões complexos
- **Content-Based Filtering**: Recomendações baseadas em gêneros e metadados
- **Hybrid Approach**: Combina múltiplas estratégias com pesos dinâmicos
- **Diversity Optimization**: Re-ranking para garantir variedade nas sugestões

### 👥 **Perfis de Usuário**
- Classificação automática: Cold Start → New → Casual → Active → Power User
- Gêneros favoritos calculados automaticamente
- Análise de comportamento e padrões de avaliação
- Métricas de atividade e engajamento

### 📊 **Analytics & Insights**
- Explicabilidade de recomendações (por que este filme foi sugerido?)
- Métricas de diversidade (gêneros, popularidade, anos)
- Estatísticas de usuários e filmes
- Performance tracking de modelos

### 🔧 **Recursos Técnicos**
- RESTful API com documentação interativa (Swagger)
- Cache inteligente com Redis
- Connection pooling e otimizações de queries
- Rate limiting e tratamento de erros
- Logging estruturado
- Health checks

---

## 🏗️ **Architecture**

O projeto segue **Clean Architecture** com Domain-Driven Design (DDD):

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│              (FastAPI Routes, DTOs, Schemas)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│     (Use Cases, Commands, Queries, Services)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  (Entities, Value Objects, Domain Services, Events)          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                        │
│  (PostgreSQL, Redis, ML Models, External Services)           │
└─────────────────────────────────────────────────────────────┘
```

### **Por que essa arquitetura?**

✅ **Testabilidade**: Domain layer 100% testável sem dependências externas  
✅ **Manutenibilidade**: Mudanças em infraestrutura não afetam regras de negócio  
✅ **Escalabilidade**: Fácil adicionar novos modelos de ML ou fontes de dados  
✅ **Independência**: Domain não conhece FastAPI, PostgreSQL ou frameworks  

---

## 🚀 **Quick Start**

### **Pré-requisitos**
- Python 3.10+
- PostgreSQL 14+
- Redis 7+

### **1. Clone o repositório**
```bash
git clone https://github.com/Isaque-Sangley/recolab-v2.git
cd recolab-v2/backend
```

### **2. Instale dependências**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### **3. Configure variáveis de ambiente**
```bash
cp .env.example .env
# Edite .env com suas configurações
```

### **4. Rode migrações**
```bash
alembic upgrade head
```

### **5. Carregue dados de exemplo**
```bash
python scripts/load_movielens.py
```

### **6. Inicie o servidor**
```bash
python run.py
```

API estará disponível em: http://localhost:8000

📚 Documentação interativa: http://localhost:8000/docs

---

## 📖 **API Documentation**

### **Principais Endpoints**

#### 🎯 **Recomendações**
```http
POST /api/v1/recommendations/
Content-Type: application/json

{
  "user_id": 1,
  "n_recommendations": 10,
  "strategy": "adaptive",
  "diversity_weight": 0.3
}
```

**Response:**
```json
{
  "user_id": 1,
  "recommendations": [
    {
      "movie_id": 318,
      "score": 0.95,
      "rank": 1,
      "movie_title": "Shawshank Redemption",
      "movie_genres": ["Drama"],
      "explanation": "Alta compatibilidade com seus filmes favoritos"
    }
  ],
  "strategy_used": "multi_stage",
  "diversity_score": 1.8
}
```

#### ⭐ **Criar Rating**
```http
POST /api/v1/ratings/
Content-Type: application/json

{
  "user_id": 1,
  "movie_id": 318,
  "score": 4.5
}
```

#### 🎬 **Buscar Filmes**
```http
GET /api/v1/movies/search/?q=matrix&limit=10
GET /api/v1/movies/popular/list?limit=20
GET /api/v1/movies/filter/?genres=Action,Sci-Fi&min_rating=4.0
```

#### 👤 **Perfil do Usuário**
```http
GET /api/v1/users/{user_id}/profile
GET /api/v1/users/{user_id}/ratings
```

### **Documentação Completa**

Acesse http://localhost:8000/docs para documentação interativa com Swagger UI.

---

## 🛠️ **Tech Stack**

### **Backend**
- **FastAPI** - Framework web moderno e rápido
- **Python 3.11** - Linguagem principal
- **SQLAlchemy 2.0** - ORM assíncrono
- **PostgreSQL** - Banco de dados principal
- **Redis** - Cache e sessões
- **Alembic** - Migrations

### **Machine Learning**
- **PyTorch** - Deep Learning framework
- **Scikit-learn** - Algoritmos clássicos de ML
- **Pandas/NumPy** - Manipulação de dados
- **Neural CF** - Collaborative Filtering com redes neurais

### **DevOps & Quality**
- **Docker & Docker Compose** - Containerização
- **GitHub Actions** - CI/CD pipeline
- **Pytest** - Framework de testes (140+ testes)
- **Black/Flake8/isort** - Code quality
- **Codecov** - Coverage tracking

### **Monitoring & Observability**
- **Prometheus** (planejado) - Métricas
- **Grafana** (planejado) - Dashboards
- **Sentry** (planejado) - Error tracking

---

## 📊 **Performance**

| Métrica | Valor |
|---------|-------|
| Latência média (recomendações) | ~450ms |
| Throughput | ~200 req/s |
| Cobertura de testes | 85%+ |
| Cold start handling | ✅ |
| Cache hit rate | ~70% |

---

## 🧪 **Testing**

O projeto possui uma suite de testes abrangente:

```bash
# Rodar todos os testes
make test

# Apenas testes unitários (rápidos)
make test-unit

# Testes de integração
make test-integration

# Com coverage
make coverage
```

**Estrutura de testes:**
- ✅ 90+ testes unitários (Domain & Services)
- ✅ 50+ testes de integração (API & Database)
- ✅ Fixtures reutilizáveis
- ✅ Mocks para dependências externas
- ✅ 85%+ code coverage

---

## 🔄 **Development Workflow**

```bash
# Setup inicial
make setup

# Durante desenvolvimento
make format          # Formata código
make lint           # Verifica qualidade
make test           # Roda testes
make ci             # Simula CI localmente

# Limpar cache
make clean
```

---

## 📈 **Roadmap**

### ✅ **Fase 1: MVP (Concluído)**
- [x] Clean Architecture com DDD
- [x] Neural Collaborative Filtering
- [x] Sistema híbrido de recomendações
- [x] API RESTful completa
- [x] Testes abrangentes
- [x] CI/CD pipeline

### 🚧 **Fase 2: Otimizações (Em Progresso)**
- [ ] Cache distribuído avançado
- [ ] A/B testing framework
- [ ] Model versioning
- [ ] Feature store

### 🔮 **Fase 3: Features Avançadas (Planejado)**
- [ ] Recomendações em tempo real (WebSockets)
- [ ] Multi-armed bandit para exploration
- [ ] Context-aware recommendations
- [ ] Social features (amigos, grupos)

---

## 🤝 **Contributing**

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/amazing-feature`
3. Commit suas mudanças: `git commit -m 'feat: add amazing feature'`
4. Push para a branch: `git push origin feature/amazing-feature`
5. Abra um Pull Request

**Convenções:**
- Commits seguem [Conventional Commits](https://www.conventionalcommits.org/)
- Code style: Black (100 chars)
- Testes são obrigatórios para novas features

---

## 🎓 **Why This Project?**

### **Para Recrutadores:**

Este projeto demonstra:

✅ **Arquitetura de Software**: Clean Architecture, DDD, SOLID principles  
✅ **Machine Learning em Produção**: Deployment de modelos, serving, monitoring  
✅ **Best Practices**: Testes, CI/CD, code quality, documentação  
✅ **Sistemas Distribuídos**: Cache, async I/O, connection pooling  
✅ **Problem Solving**: Desafios reais (cold start, diversity, performance)  

### **Diferenciais:**

🔥 **Não é um projeto tutorial** - Arquitetura profissional  
🔥 **Testes reais** - 140+ testes com 85%+ coverage  
🔥 **Documentação completa** - README, docstrings, API docs  
🔥 **CI/CD funcional** - Pipeline automatizado  
🔥 **Código limpo** - Formatado, lintado, revisado  

---

## 📚 **Documentação Adicional**

- [Arquitetura Detalhada](docs/ARCHITECTURE.md)
- [Guia de Contribuição](docs/CONTRIBUTING.md)
- [ADRs (Architecture Decision Records)](docs/adr/)
- [API Reference](docs/API.md)

---

## 📝 **License**

Este projeto está sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 **Autor**

**Isaque Sangley dos Santos Gomes**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/isaque-sangley-6a1044217)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Isaque-Sangley)
[![Portfolio](https://img.shields.io/badge/Portfolio-FF5722?style=for-the-badge&logo=google-chrome&logoColor=white)](https://isaquesangley.com)

---

<div align="center">

**Se este projeto foi útil, deixe uma ⭐!**

Desenvolvido com ❤️ e ☕ (mentira, sem ☕)

</div>