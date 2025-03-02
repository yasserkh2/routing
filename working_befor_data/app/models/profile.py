from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from .link import Link

@dataclass
class Profile:
    """Represents a routing profile with its properties"""
    profile_id: str
    name: str
    expected_sla: float
    priority: str
    links: List[Link]
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any], available_links: List[Link]) -> 'Profile':
        """Create a Profile instance from API data"""
        # Get links assigned to this profile
        profile_links = [
            link for link in available_links 
            if link.link_id in data['links']
        ]
        
        return cls(
            profile_id=data['profile_id'],
            name=data['name'],
            expected_sla=float(data['expected_sla']),
            priority=data['priority'],
            links=profile_links
        )

    @classmethod
    def get_profiles_affected_by_price_change(cls, profiles: List['Profile'], link_id: str) -> List['Profile']:
        """Get all profiles that contain the link with price change"""
        return [
            profile for profile in profiles
            if any(link.link_id == link_id for link in profile.links)
        ]
    
    def update_link_price(self, link_id: str, new_price: float) -> bool:
        """Update price for a specific link in the profile"""
        link = self.get_link_by_id(link_id)
        if link:
            updated_link = link.with_updated_price(new_price)
            self.remove_link(link_id)
            self.add_link(updated_link)
            return True
        return False
    
    def to_optimizer_format(self) -> Dict[str, Any]:
        """Convert profile data to format needed by optimizer"""
        links_data = {}
        for link in self.links:
            if link.average_sla > 0:
                links_data[link.link_id] = link.to_optimizer_format()
                
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'expected_sla': self.expected_sla,
            'links': links_data
        }
    
    def get_active_links(self) -> List[Link]:
        """Get all active links that meet the profile's SLA requirement"""
        return [
            link for link in self.links 
            if link.meets_sla_requirement(self.expected_sla)
        ]
    
    def get_link_by_id(self, link_id: str) -> Optional[Link]:
        """Get a link by its ID"""
        for link in self.links:
            if link.link_id == link_id:
                return link
        return None
    
    def add_link(self, link: Link) -> None:
        """Add a new link to the profile"""
        if not any(existing.link_id == link.link_id for existing in self.links):
            self.links.append(link)
    
    def remove_link(self, link_id: str) -> bool:
        """Remove a link from the profile by its ID"""
        initial_length = len(self.links)
        self.links = [link for link in self.links if link.link_id != link_id]
        return len(self.links) < initial_length
    
    def get_links_by_operator(self, operator: str) -> List[Link]:
        """Get all links for a specific operator"""
        return [link for link in self.links if link.operator == operator]
    
    def get_links_by_mnc(self, mnc: str) -> List[Link]:
        """Get all links for a specific MNC"""
        return [link for link in self.links if link.mnc == mnc]