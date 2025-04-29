import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
from .event_handler import EventHandler, Event
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class BaseMockAPIService(ABC):
    """Abstract base class for mock API services"""
    
    def __init__(self):
        self.mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
        self.event_handler = EventHandler()
        logger.info(f"BaseMockAPIService initialized with mock data directory: {self.mock_data_dir}")
    
    def _read_json_file(self, filename: str) -> Dict:
        """Helper method to read JSON files from mock_data directory"""
        file_path = os.path.join(self.mock_data_dir, filename)
        logger.debug(f"Reading JSON file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.debug(f"Successfully read JSON file: {filename}")
            return data
        except Exception as e:
            logger.error(f"Failed to read JSON file {filename}: {str(e)}", exc_info=True)
            raise
    
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