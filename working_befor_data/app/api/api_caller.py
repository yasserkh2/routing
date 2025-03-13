from typing import Dict, Any
from ..services.event_handler import Event
from .api_interfaces import APIClient, APIResponse, APIExecutor
from ..utils.logger import setup_logger
import json
import os
import asyncio

# Setup logger
logger = setup_logger(__name__)

class APICaller:
    """
    Calls all available APIs and aggregates their responses.
    """
    
    def __init__(self):
        self.mock_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mock_data')
        logger.info("APICaller initialized with mock data directory: %s", self.mock_data_dir)
    
    async def call_all_apis(self, event: Event) -> Dict[str, Any]:
        """Execute all available API calls"""
        logger.info(f"Starting API calls for event type: {event.type}")
        results = {}
        
        # Get links data
        logger.info(f"Fetching links data for event (MNC: {event.mnc})")
        results['links_data'] = await self._get_links_data(event)
        
        # Get profile configurations
        logger.info("Fetching profile configurations")
        results['profile_config'] = await self._get_profile_config(event)
        
        # Add metadata
        event.add_metadata('apis_called', len(results))
        event.add_metadata('processing_complete', True)
        
        logger.info(f"Completed all API calls. Total APIs called: {len(results)}")
        return results

    async def _get_links_data(self, event: Event) -> APIResponse:
        """Get comprehensive data for links"""
        try:
            # Read from links_data.json asynchronously
            file_path = os.path.join(self.mock_data_dir, 'links_data.json')
            logger.debug(f"Reading links data from: {file_path}")
            
            def read_json():
                with open(file_path, 'r') as f:
                    return json.load(f)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, read_json)
                
            logger.info(f"Retrieved {len(data)} links")
                
            return APIResponse(data=data, success=True, error=None)
        except Exception as e:
            logger.error(f"Failed to get links data: {str(e)}", exc_info=True)
            return APIResponse(data={}, success=False, error=str(e))

    async def _get_profile_config(self, event: Event) -> APIResponse:
        """Get profile configurations"""
        try:
            # Read from profiles.json asynchronously
            file_path = os.path.join(self.mock_data_dir, 'profiles.json')
            logger.debug(f"Reading profile configurations from: {file_path}")
            
            def read_json():
                with open(file_path, 'r') as f:
                    return json.load(f)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, read_json)
                
            logger.info(f"Retrieved {len(data)} profiles")
                
            return APIResponse(data=data, success=True, error=None)
        except Exception as e:
            logger.error(f"Failed to get profile configurations: {str(e)}", exc_info=True)
            return APIResponse(data={}, success=False, error=str(e))
            
    def _read_json_file(self, file_path: str) -> dict:
        """Helper method to read JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)