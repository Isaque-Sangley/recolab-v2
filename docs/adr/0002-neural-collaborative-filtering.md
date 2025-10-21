# ADR 0003: Implementação de Neural Collaborative Filtering para Recomendações

## Status

Aceito

## Contexto

O sistema precisa gerar recomendações personalizadas baseadas em padrões implícitos de comportamento dos usuários. Os requisitos principais são:

1. Capturar interações não-lineares entre usuários e filmes
2. Lidar com cold start (novos usuários/filmes)
3. Escalar para milhões de usuários e dezenas de milhares de filmes
4. Performance de inferência < 500ms para 10 recomendações
5. Facilidade de retreinamento com novos dados

Técnicas tradicionais de Collaborative Filtering apresentam limitações:

**Matrix Factorization (SVD, ALS)**
- Assume interações lineares entre fatores latentes
- Não captura relações complexas
- Difícil adicionar features contextuais (horário, dispositivo)

**Item-based/User-based KNN**
- Não escala bem para datasets grandes
- Sparsity problem em matrizes user-item
- Difícil fazer feature engineering

**Content-Based Filtering**
- Ignora colaboração entre usuários
- Limitado à similaridade de features dos itens

## Decisão

Implementar Neural Collaborative Filtering (NCF) usando PyTorch, combinando:

**Arquitetura do Modelo**
```
Input Layer:
├── User ID → User Embedding (dim=64)
└── Movie ID → Movie Embedding (dim=64)

Neural CF Layers:
├── GMF Path (Generalized Matrix Factorization)
│   └── Element-wise Product → Linear
└── MLP Path (Multi-Layer Perceptron)
    └── Concat → FC(128) → FC(64) → FC(32)

Fusion Layer:
└── Concat(GMF, MLP) → FC(16) → Output(1)

Output:
└── Sigmoid → Rating Prediction [0, 1]
```

**Componentes Técnicos**

1. **Embeddings Aprendidos**: User_id e movie_id mapeados para vetores densos de 64 dimensões

2. **Dual Path Architecture**:
   - GMF: Captura interações lineares (similar a MF tradicional)
   - MLP: Captura interações não-lineares complexas

3. **Loss Function**: MSE para regression de ratings [0.5, 5.0] normalizados para [0, 1]

4. **Regularização**:
   - Dropout (p=0.2) nas camadas MLP
   - Weight Decay (L2 regularization)
   - Early stopping baseado em validation loss

5. **Training Strategy**:
   - Mini-batch gradient descent (batch_size=1024)
   - Adam optimizer (lr=0.001)
   - Learning rate scheduler (ReduceLROnPlateau)

## Consequências

### Positivas

1. **Captura de Padrões Complexos**: MLP layers permitem modelar interações não-lineares que MF tradicional não consegue.

2. **Flexibilidade**: Fácil adicionar features contextuais (timestamp, gêneros favoritos) expandindo o input.

3. **Performance de Inferência**: Após treinamento, predição é apenas forward pass, ~200ms para 100 filmes.

4. **State-of-the-Art**: Arquitetura baseada em paper do He et al. (2017) amplamente validado academicamente.

5. **Framework Moderno**: PyTorch oferece debugging fácil, gradientes automáticos, GPU acceleration.

6. **Transferência de Aprendizado**: Embeddings aprendidos podem ser reutilizados para outras tasks (clustering, visualização).

### Negativas

1. **Cold Start Persiste**: Novos usuários/filmes sem embeddings treinados. Mitigado com content-based fallback.

2. **Requisito Computacional**: Treinamento requer GPU (NVIDIA T4 no mínimo). Mitigado com Google Colab para MVP.

3. **Complexidade de Deploy**: Modelo neural é mais pesado que matriz de similaridade. Requer modelo serving infrastructure.

4. **Interpretabilidade Limitada**: Embeddings são black-box. Difícil explicar "por que este filme foi recomendado".

5. **Data Hungry**: Precisa de ~10k ratings para convergir. Dataset MovieLens 100k é suficiente para MVP.

## Alternativas Consideradas

### Matrix Factorization (SVD/ALS)
**Rejeitado**:
- Assume linearidade nos fatores latentes
- Performance inferior em benchmarks (RMSE ~15% pior que NCF)
- Não permite fácil incorporação de features adicionais

**Casos onde seria melhor**: Quando interpretabilidade é crítica (bancos, healthcare)

### Deep Factorization Machines (DeepFM)
**Considerado**:
- Excelente para CTR prediction com features categóricas
- Mais complexo que necessário para nosso caso
- Reservado para versão futura com muitas features contextuais

### Graph Neural Networks (GNN)
**Rejeitado para MVP**:
- Estado da arte mais recente (LightGCN, NGCF)
- Requer graph construction (computacionalmente caro)
- Complexidade de implementação alta
- Considerado para v3.0 quando escalarmos para grafos sociais

### Transformer-based (BERT4Rec, SASRec)
**Rejeitado**:
- Excelente para sequências (próximo filme a assistir)
- Nosso caso não tem forte componente temporal
- Overhead computacional significativo
- Considerado se adicionarmos feature de "continuar assistindo"

### AutoML (AutoRec, NeuMF-AutoML)
**Rejeitado**:
- Busca de arquitetura automatizada é computacionalmente cara
- Arquitetura NeuMF manual já é baseline forte
- Prematura otimização para MVP

## Implementação

**Model Serving**:
```python
class NeuralCFModel:
    def __init__(self, n_users, n_movies, embedding_dim=64):
        self.user_embedding = nn.Embedding(n_users, embedding_dim)
        self.movie_embedding = nn.Embedding(n_movies, embedding_dim)
        
        # GMF path
        self.gmf_layer = nn.Linear(embedding_dim, 1)
        
        # MLP path
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim * 2, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU()
        )
        
        # Fusion
        self.fusion = nn.Linear(32 + 1, 1)
        self.sigmoid = nn.Sigmoid()
```

**Training Pipeline**:
1. Load MovieLens 100k dataset
2. Train/validation/test split (80/10/10)
3. Train for 50 epochs with early stopping (patience=5)
4. Save best model checkpoint
5. Evaluate on test set (target RMSE < 0.85)

**Model Versioning**:
- Armazenado no ModelRepository (PostgreSQL metadata + filesystem artifacts)
- Versionamento semântico (v1.0.0, v1.1.0)
- A/B testing entre versões via feature flag

## Métricas de Sucesso

- RMSE < 0.85 no MovieLens 100k test set
- Latência de inferência < 200ms para 100 predições
- Diversity score > 0.6 (evitar filter bubble)
- Coverage > 50% (% de filmes recomendados pelo menos uma vez)