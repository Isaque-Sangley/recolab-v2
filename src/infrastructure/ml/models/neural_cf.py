"""
Neural Collaborative Filtering (NCF)

Implementação em PyTorch do paper:
"Neural Collaborative Filtering" (He et al., 2017)

Arquitetura:
- Embedding layers para users e items
- MLP (Multi-Layer Perceptron) para aprender interações
- Otimizado para implicit feedback (mas adaptamos para ratings)
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import pickle

from .base import BaseRecommendationModel


class NCFDataset(Dataset):
    """
    Dataset para PyTorch DataLoader.
    
    Converte dados de recomendação em formato para treino.
    """
    
    def __init__(self, user_ids: np.ndarray, item_ids: np.ndarray, ratings: np.ndarray):
        """
        Args:
            user_ids: array de user IDs
            item_ids: array de item IDs
            ratings: array de ratings (0-5)
        """
        self.user_ids = torch.LongTensor(user_ids)
        self.item_ids = torch.LongTensor(item_ids)
        # Normaliza ratings para 0-1 (facilita convergência)
        self.ratings = torch.FloatTensor(ratings / 5.0)
    
    def __len__(self) -> int:
        return len(self.user_ids)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.user_ids[idx], self.item_ids[idx], self.ratings[idx]


class NCFModel(nn.Module):
    """
    Neural Network Architecture para NCF.
    
    Arquitetura:
    ┌─────────┐  ┌─────────┐
    │ User ID │  │ Item ID │
    └────┬────┘  └────┬────┘
         │            │
         ▼            ▼
    ┌─────────┐  ┌─────────┐
    │User Emb │  │Item Emb │
    └────┬────┘  └────┬────┘
         │            │
         └─────┬──────┘
               │ Concat
               ▼
         ┌──────────┐
         │   MLP    │
         │ (hidden) │
         └─────┬────┘
               │
               ▼
         ┌──────────┐
         │  Output  │
         │ (rating) │
         └──────────┘
    """
    
    def __init__(
        self,
        n_users: int,
        n_items: int,
        embedding_dim: int = 64,
        hidden_layers: List[int] = [128, 64, 32],
        dropout: float = 0.2
    ):
        """
        Args:
            n_users: número total de usuários
            n_items: número total de items
            embedding_dim: dimensão dos embeddings
            hidden_layers: lista com tamanho de cada camada oculta
            dropout: taxa de dropout (regularização)
        """
        super(NCFModel, self).__init__()
        
        self.n_users = n_users
        self.n_items = n_items
        self.embedding_dim = embedding_dim
        
        # Embedding layers
        self.user_embedding = nn.Embedding(n_users, embedding_dim)
        self.item_embedding = nn.Embedding(n_items, embedding_dim)
        
        # MLP layers
        mlp_layers = []
        input_size = embedding_dim * 2  # Concat user + item
        
        for hidden_size in hidden_layers:
            mlp_layers.append(nn.Linear(input_size, hidden_size))
            mlp_layers.append(nn.ReLU())
            mlp_layers.append(nn.Dropout(dropout))
            input_size = hidden_size
        
        # Output layer
        mlp_layers.append(nn.Linear(input_size, 1))
        mlp_layers.append(nn.Sigmoid())  # Output 0-1
        
        self.mlp = nn.Sequential(*mlp_layers)
        
        # Inicialização de pesos (importante!)
        self._init_weights()
    
    def _init_weights(self):
        """
        Inicialização Xavier/He para melhor convergência.
        """
        nn.init.normal_(self.user_embedding.weight, std=0.01)
        nn.init.normal_(self.item_embedding.weight, std=0.01)
        
        for layer in self.mlp:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.constant_(layer.bias, 0.0)
    
    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            user_ids: tensor de user IDs [batch_size]
            item_ids: tensor de item IDs [batch_size]
        
        Returns:
            Predictions [batch_size, 1]
        """
        # Embeddings
        user_emb = self.user_embedding(user_ids)  # [batch_size, embedding_dim]
        item_emb = self.item_embedding(item_ids)  # [batch_size, embedding_dim]
        
        # Concatena
        concat = torch.cat([user_emb, item_emb], dim=-1)  # [batch_size, embedding_dim*2]
        
        # MLP
        output = self.mlp(concat)  # [batch_size, 1]
        
        return output.squeeze()  # [batch_size]
    
    def get_user_embedding(self, user_id: int) -> np.ndarray:
        """Retorna embedding de um usuário"""
        with torch.no_grad():
            user_tensor = torch.LongTensor([user_id])
            embedding = self.user_embedding(user_tensor)
            return embedding.cpu().numpy()[0]
    
    def get_item_embedding(self, item_id: int) -> np.ndarray:
        """Retorna embedding de um item"""
        with torch.no_grad():
            item_tensor = torch.LongTensor([item_id])
            embedding = self.item_embedding(item_tensor)
            return embedding.cpu().numpy()[0]


class NeuralCF(BaseRecommendationModel):
    """
    Neural Collaborative Filtering - Implementação completa.
    
    Características:
    - Deep learning com PyTorch
    - Embeddings aprendidos
    - MLP para capturar interações não-lineares
    - Mini-batch training
    - Early stopping
    - GPU support (se disponível)
    """
    
    def __init__(
        self,
        embedding_dim: int = 64,
        hidden_layers: List[int] = [128, 64, 32],
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 256,
        epochs: int = 20,
        device: str = None
    ):
        """
        Args:
            embedding_dim: dimensão dos embeddings
            hidden_layers: arquitetura MLP
            dropout: taxa de dropout
            learning_rate: taxa de aprendizado
            batch_size: tamanho do batch
            epochs: número de épocas
            device: 'cuda', 'cpu' ou None (auto-detect)
        """
        self.embedding_dim = embedding_dim
        self.hidden_layers = hidden_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        
        # Auto-detect GPU
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"🔧 Using device: {self.device}")
        
        self.model: Optional[NCFModel] = None
        self.user_id_map: Dict[int, int] = {}
        self.item_id_map: Dict[int, int] = {}
        self.reverse_item_map: Dict[int, int] = {}
        self.n_users: int = 0
        self.n_items: int = 0
        self.is_fitted: bool = False
    
    def fit(
        self,
        user_ids: np.ndarray,
        item_ids: np.ndarray,
        ratings: np.ndarray
    ) -> Dict[str, float]:
        """
        Treina o modelo NCF.
        
        Args:
            user_ids: array de user IDs
            item_ids: array de item IDs  
            ratings: array de ratings (0-5)
        
        Returns:
            Dict com métricas de treinamento
        """
        print(f"🚀 Training NCF model...")
        print(f"   - Samples: {len(user_ids)}")
        print(f"   - Epochs: {self.epochs}")
        print(f"   - Batch size: {self.batch_size}")
        
        # Cria mapeamentos ID → índice (0, 1, 2, ...)
        unique_users = np.unique(user_ids)
        unique_items = np.unique(item_ids)
        
        self.user_id_map = {uid: idx for idx, uid in enumerate(unique_users)}
        self.item_id_map = {iid: idx for idx, iid in enumerate(unique_items)}
        self.reverse_item_map = {idx: iid for iid, idx in self.item_id_map.items()}
        
        self.n_users = len(unique_users)
        self.n_items = len(unique_items)
        
        # Converte IDs para índices
        user_indices = np.array([self.user_id_map[uid] for uid in user_ids])
        item_indices = np.array([self.item_id_map[iid] for iid in item_ids])
        
        # Cria dataset e dataloader
        dataset = NCFDataset(user_indices, item_indices, ratings)
        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=0  # 0 para evitar problemas no Windows
        )
        
        # Cria modelo
        self.model = NCFModel(
            n_users=self.n_users,
            n_items=self.n_items,
            embedding_dim=self.embedding_dim,
            hidden_layers=self.hidden_layers,
            dropout=self.dropout
        ).to(self.device)
        
        # Loss e optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Training loop
        best_loss = float('inf')
        patience = 3
        patience_counter = 0
        
        history = {
            'train_loss': [],
            'epochs_trained': 0
        }
        
        for epoch in range(self.epochs):
            self.model.train()
            epoch_loss = 0.0
            n_batches = 0
            
            for batch_users, batch_items, batch_ratings in dataloader:
                # Move to device
                batch_users = batch_users.to(self.device)
                batch_items = batch_items.to(self.device)
                batch_ratings = batch_ratings.to(self.device)
                
                # Forward pass
                predictions = self.model(batch_users, batch_items)
                loss = criterion(predictions, batch_ratings)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                n_batches += 1
            
            avg_loss = epoch_loss / n_batches
            history['train_loss'].append(avg_loss)
            
            print(f"   Epoch {epoch+1}/{self.epochs} - Loss: {avg_loss:.4f}")
            
            # Early stopping
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(f"   ⚠️  Early stopping at epoch {epoch+1}")
                    break
        
        history['epochs_trained'] = epoch + 1
        history['final_loss'] = avg_loss
        history['best_loss'] = best_loss
        
        self.is_fitted = True
        
        print(f"✅ Training complete!")
        print(f"   - Final loss: {avg_loss:.4f}")
        print(f"   - Best loss: {best_loss:.4f}")
        
        return history
    
    def predict(self, user_id: int, item_id: int) -> float:
        """
        Prediz rating para um par user-item.
        
        Args:
            user_id: ID do usuário
            item_id: ID do item
        
        Returns:
            Rating predito (0-5)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted yet!")
        
        # Cold start
        if user_id not in self.user_id_map or item_id not in self.item_id_map:
            return 3.0  # Média neutra
        
        self.model.eval()
        
        with torch.no_grad():
            user_idx = self.user_id_map[user_id]
            item_idx = self.item_id_map[item_id]
            
            user_tensor = torch.LongTensor([user_idx]).to(self.device)
            item_tensor = torch.LongTensor([item_idx]).to(self.device)
            
            prediction = self.model(user_tensor, item_tensor)
            
            # Converte de 0-1 para 0-5
            rating = prediction.cpu().item() * 5.0
            
            return float(np.clip(rating, 0.0, 5.0))
    
    def recommend(
        self,
        user_id: int,
        n_recommendations: int = 10,
        exclude_items: List[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Gera top-N recomendações para um usuário.
        
        Estratégia:
        - Calcula score para TODOS os items
        - Ordena por score
        - Retorna top-N
        
        Args:
            user_id: ID do usuário
            n_recommendations: número de recomendações
            exclude_items: itens a excluir
        
        Returns:
            Lista de (item_id, score) ordenada por score DESC
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted yet!")
        
        # Cold start - retorna itens populares
        if user_id not in self.user_id_map:
            return []
        
        exclude_items = exclude_items or []
        exclude_set = set(exclude_items)
        
        self.model.eval()
        
        with torch.no_grad():
            user_idx = self.user_id_map[user_id]
            
            # Cria tensors para todos os items
            n_items = self.n_items
            user_tensor = torch.LongTensor([user_idx] * n_items).to(self.device)
            item_tensor = torch.LongTensor(list(range(n_items))).to(self.device)
            
            # Prediz scores para todos
            scores = self.model(user_tensor, item_tensor)
            scores = scores.cpu().numpy()
            
            # Cria lista de (item_id, score)
            recommendations = []
            for item_idx, score in enumerate(scores):
                item_id = self.reverse_item_map[item_idx]
                
                if item_id in exclude_set:
                    continue
                
                recommendations.append((item_id, float(score)))
            
            # Ordena por score DESC
            recommendations.sort(key=lambda x: x[1], reverse=True)
            
            return recommendations[:n_recommendations]
    
    def save(self, path: str) -> None:
        """
        Salva modelo completo.
        
        Salva:
        - Estado do PyTorch model
        - Mapeamentos
        - Hiperparâmetros
        """
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        save_dict = {
            'model_state_dict': self.model.state_dict(),
            'user_id_map': self.user_id_map,
            'item_id_map': self.item_id_map,
            'reverse_item_map': self.reverse_item_map,
            'n_users': self.n_users,
            'n_items': self.n_items,
            'embedding_dim': self.embedding_dim,
            'hidden_layers': self.hidden_layers,
            'dropout': self.dropout
        }
        
        torch.save(save_dict, path)
        print(f"💾 Model saved to {path}")
    
    def load(self, path: str) -> None:
        """Carrega modelo do disco"""
        save_dict = torch.load(path, map_location=self.device)
        
        # Restaura hiperparâmetros
        self.embedding_dim = save_dict['embedding_dim']
        self.hidden_layers = save_dict['hidden_layers']
        self.dropout = save_dict['dropout']
        self.user_id_map = save_dict['user_id_map']
        self.item_id_map = save_dict['item_id_map']
        self.reverse_item_map = save_dict['reverse_item_map']
        self.n_users = save_dict['n_users']
        self.n_items = save_dict['n_items']
        
        # Recria modelo
        self.model = NCFModel(
            n_users=self.n_users,
            n_items=self.n_items,
            embedding_dim=self.embedding_dim,
            hidden_layers=self.hidden_layers,
            dropout=self.dropout
        ).to(self.device)
        
        # Carrega pesos
        self.model.load_state_dict(save_dict['model_state_dict'])
        self.model.eval()
        
        self.is_fitted = True
        
        print(f"📂 Model loaded from {path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo"""
        return {
            'type': 'neural_collaborative_filtering',
            'framework': 'pytorch',
            'n_users': self.n_users,
            'n_items': self.n_items,
            'embedding_dim': self.embedding_dim,
            'hidden_layers': self.hidden_layers,
            'dropout': self.dropout,
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'device': str(self.device),
            'is_fitted': self.is_fitted,
            'total_parameters': sum(p.numel() for p in self.model.parameters()) if self.model else 0
        }