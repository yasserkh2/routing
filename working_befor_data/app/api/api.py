from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..services.event_handler import Event

class API(ABC):
    """Abstract base class for API services"""
    
    @abstractmethod
    def handle_price_change(self, link_name: str, new_price: float, old_price: Optional[float] = None) -> Event:
        """Handle price change event for a link"""
        pass
    
    @abstractmethod
    def handle_sla_change(self, link_name: str, changed_sla: Dict[str, Dict[str, float]]) -> Event:
        """Handle SLA change event for a link"""
        pass
    
    @abstractmethod
    async def get_links_data(self, mnc: Optional[str] = None) -> List[Dict]:
        """Get comprehensive data for links"""
        pass
    
    @abstractmethod
    async def get_profile_config(self, profile_id: Optional[str] = None) -> List[Dict]:
        """Get profile configurations"""
        pass