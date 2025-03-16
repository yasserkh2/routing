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
    links: List[Link]
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any], available_links: List[Link]) -> 'Profile':
        """Create a Profile instance from API data"""
        # Get links assigned to this profile
        profile_links = [
            link for link in available_links 
            if link.link in data['links']
        ]
        
        return cls(
            profile_id=data['profile_id'],
            name=data['name'],
            expected_sla=float(data['expected_sla']),
            links=profile_links
        )

    def to_optimizer_format(self) -> Dict[str, Any]:
        """Convert profile data to format needed by optimizer"""
        links_data = {}
        for link in self.links:
            if link.average_sla > 0:
                links_data[link.link] = link.to_optimizer_format()
                
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
    
    def get_link_by_id(self, link_name: str) -> Optional[Link]:
        """Get a link by its name"""
        for link in self.links:
            if link.link == link_name:
                return link
        return None
    
    def add_link(self, link: Link) -> None:
        """Add a new link to the profile"""
        if not any(existing.link == link.link for existing in self.links):
            self.links.append(link)
    
    def remove_link(self, link_name: str) -> bool:
        """Remove a link from the profile by its name"""
        initial_length = len(self.links)
        self.links = [link for link in self.links if link.link != link_name]
        return len(self.links) < initial_length

    def clone(self) -> 'Profile':
        """Create a copy of the profile"""
        return Profile(
            profile_id=self.profile_id,
            name=self.name,
            expected_sla=self.expected_sla,
            links=[link.copy() for link in self.links]
        )
