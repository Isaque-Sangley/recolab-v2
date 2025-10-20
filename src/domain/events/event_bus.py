"""
Domain Event Bus

Gerencia publicação e subscrição de eventos.
"""

from typing import Dict, List, Callable, Any
from .base import DomainEvent


class DomainEventBus:
    """
    Event Bus para eventos de domínio.
    
    Pattern: Publish-Subscribe
    - Publishers publicam eventos
    - Subscribers escutam eventos específicos
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[DomainEvent] = []
    
    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """
        Subscreve a um tipo de evento.
        
        Args:
            event_type: tipo do evento (ex: "user.created")
            handler: função que processa o evento
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publica um evento.
        
        Args:
            event: evento a ser publicado
        """
        # Salva no histórico
        self._event_history.append(event)
        
        # Notifica subscribers
        if event.event_type in self._subscribers:
            for handler in self._subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"❌ Error in event handler: {e}")
    
    def get_event_history(self) -> List[DomainEvent]:
        """Retorna histórico de eventos"""
        return self._event_history.copy()
    
    def clear_history(self) -> None:
        """Limpa histórico de eventos"""
        self._event_history.clear()