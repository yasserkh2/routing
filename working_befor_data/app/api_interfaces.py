from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from event_handler import Event

class APIResponse:
    """Value object for API responses"""
    def __init__(self, data: Dict[str, Any], success: bool, error: Optional[str] = None):
        self.data = data
        self.success = success
        self.error = error
        self.timestamp = None

class APIClient(ABC):
    """Abstract base class for API clients"""
    @abstractmethod
    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make API call"""
        pass

class APICallStrategy(ABC):
    """Abstract base class for API call strategies"""
    @abstractmethod
    async def call_api(self, event: Event) -> APIResponse:
        """Execute the API call based on the event"""
        pass

    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """Check if strategy can handle this event"""
        pass

class APIStrategyFactory(ABC):
    """Abstract factory for creating API strategies"""
    @abstractmethod
    def create_strategy(self, strategy_type: str) -> APICallStrategy:
        """Create a strategy instance"""
        pass

class APIExecutor(ABC):
    """Abstract base class for executing API strategies"""
    @abstractmethod
    async def execute(self, strategy: APICallStrategy, event: Event) -> APIResponse:
        """Execute a strategy"""
        pass

class APIRegistry(ABC):
    """Abstract base class for strategy registry"""
    @abstractmethod
    def register_strategy(self, event_type: str, strategy: APICallStrategy) -> None:
        """Register a strategy"""
        pass

    @abstractmethod
    def get_strategies(self, event: Event) -> list[APICallStrategy]:
        """Get strategies for an event"""
        pass