from typing import Dict, List, Any, Type
from event_handler import Event, EventType
from api_interfaces import (
    APICallStrategy,
    APIRegistry,
    APIExecutor,
    APIResponse,
    APIClient
)
from api_strategy import (
    DefaultAPIStrategyFactory,
    GetProfilesRelatedToLinkStrategy,
    GetLinksSLAByMNCStrategy,
    GetProfilesWithLinksStrategy,
    RouteDetailsAPIStrategy
)

class DefaultAPIRegistry(APIRegistry):
    """Registry for API strategies"""
    
    def __init__(self, strategy_factory: DefaultAPIStrategyFactory):
        self._strategy_factory = strategy_factory
        self._strategies: Dict[EventType, List[Type[APICallStrategy]]] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self) -> None:
        """Initialize default strategy mappings for price change events"""
        self._strategies = {
            EventType.PRICE_CHANGE: [
                # First get route details
                RouteDetailsAPIStrategy,
                # Query1: Get profiles related to link
                GetProfilesRelatedToLinkStrategy,
                # Query2: Get all links' SLA data for the MNC
                GetLinksSLAByMNCStrategy,
                # Query3: Get all profiles with their associated links
                GetProfilesWithLinksStrategy
            ]
        }
    
    def register_strategy(self, event_type: EventType, strategy: Type[APICallStrategy]) -> None:
        """Register a new strategy for an event type"""
        if event_type not in self._strategies:
            self._strategies[event_type] = []
        
        if strategy not in self._strategies[event_type]:
            self._strategies[event_type].append(strategy)
    
    def get_strategies(self, event: Event) -> List[APICallStrategy]:
        """Get list of instantiated strategy objects for an event"""
        if event.event_type not in self._strategies:
            return []
        
        strategies = []
        for strategy_class in self._strategies[event.event_type]:
            strategy = self._strategy_factory.create_strategy(strategy_class)
            if strategy.can_handle(event):
                strategies.append(strategy)
        
        return strategies

class DefaultAPIExecutor(APIExecutor):
    """Executor for API strategies"""
    
    async def execute(self, strategy: APICallStrategy, event: Event) -> APIResponse:
        """Execute a single strategy"""
        try:
            response = await strategy.call_api(event)
            
            # Add metadata about the execution
            strategy_name = strategy.__class__.__name__
            event.add_metadata(f"{strategy_name}_success", response.success)
            if response.error:
                event.add_metadata(f"{strategy_name}_error", response.error)
            if response.timestamp:
                event.add_metadata(f"{strategy_name}_timestamp", response.timestamp)
            
            return response
            
        except Exception as e:
            # Handle any unexpected errors
            strategy_name = strategy.__class__.__name__
            event.add_metadata(f"{strategy_name}_error", str(e))
            event.add_metadata(f"{strategy_name}_success", False)
            return APIResponse(data={}, success=False, error=str(e))

class APISelector:
    """
    Coordinates API strategy selection and execution.
    Uses registry and executor components for better separation of concerns.
    """
    
    def __init__(self, 
                 registry: APIRegistry = None,
                 executor: APIExecutor = None,
                 api_client: APIClient = None):
        strategy_factory = DefaultAPIStrategyFactory(api_client)
        self._registry = registry or DefaultAPIRegistry(strategy_factory)
        self._executor = executor or DefaultAPIExecutor()
    
    async def execute_strategies(self, event: Event) -> Dict[str, Any]:
        """Execute all applicable strategies for an event"""
        results = {}
        strategies = self._registry.get_strategies(event)
        
        for strategy in strategies:
            response = await self._executor.execute(strategy, event)
            if response.success:
                results[strategy.__class__.__name__] = response.data
        
        # Add summary metadata
        event.add_metadata('apis_called', len(results))
        event.add_metadata('processing_complete', True)
        
        return results

    def analyze_strategies(self, event: Event) -> Dict[str, Any]:
        """Analyze which strategies will be executed for an event"""
        strategies = self._registry.get_strategies(event)
        return {
            "event_type": event.event_type.name,
            "strategies": [strategy.__class__.__name__ for strategy in strategies],
            "strategy_count": len(strategies)
        }

# Note: This implementation follows SOLID principles and includes three main queries:
# Query1: GetProfilesRelatedToLink(link, mnc) -> profilesWithLinks
# Query2: GetLinksSLAByMNC(mnc) -> links with their SLA data
# Query3: GetProfilesWithLinks() -> profiles with their associated links