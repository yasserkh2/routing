from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..services.event_handler import Event
from datetime import datetime
from ..utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class APIResponse:
    """Value object for API responses"""
    def __init__(self, data: Dict[str, Any], success: bool, error: Optional[str] = None):
        self.data = data
        self.success = success
        self.error = error
        self.timestamp = datetime.utcnow()
        if success:
            logger.info(f"API Response created successfully at {self.timestamp}")
        else:
            logger.error(f"API Response created with error: {error}")

class APIClient(ABC):
    """Abstract base class for API clients"""
    @abstractmethod
    async def call(self, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Make API call"""
        pass

class APIExecutor:
    """Base class for executing API calls"""
    async def execute(self, api_client: APIClient, endpoint: str, params: Dict[str, Any]) -> APIResponse:
        """Execute an API call"""
        try:
            logger.info(f"Executing API call to endpoint: {endpoint}")
            logger.debug(f"API call parameters: {params}")
            
            response = await api_client.call(endpoint, params)
            
            if response.success:
                logger.info(f"API call to {endpoint} completed successfully")
                logger.debug(f"API response data: {response.data}")
            else:
                logger.warning(f"API call to {endpoint} completed with errors: {response.error}")
            
            return response
        except Exception as e:
            error_msg = f"API call to {endpoint} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return APIResponse(data={}, success=False, error=error_msg)