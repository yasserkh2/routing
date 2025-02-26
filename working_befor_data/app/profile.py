from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from link import Link

@dataclass
class Profile:
    """Represents a routing profile with its properties"""
    profile_id: str
    name: str
    expected_sla: float
    priority: str
    links: List[Link]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create a Profile instance from a dictionary"""
        links = [Link.from_dict(link_data) for link_data in data.get('links', [])]
        return cls(
            profile_id=data['profile_id'],
            name=data['name'],
            expected_sla=data['expected_sla'],
            priority=data['priority'],
            links=links
        )

    def get_active_links(self) -> List[Link]:
        """Get all active links that meet the profile's SLA requirement"""
        return [
            link for link in self.links 
            if link.is_usable() and link.meets_sla_requirement(self.expected_sla)
        ]

    def get_best_link(self) -> Optional[Link]:
        """Get the best available link based on routing priority and SLA"""
        active_links = self.get_active_links()
        if not active_links:
            return None
            
        # Sort by routing priority (lower is better) and effective SLA (higher is better)
        return sorted(
            active_links,
            key=lambda link: (
                link.routing_priority,
                -(link.get_effective_sla() or 0)
            )
        )[0]

    def to_dict(self) -> Dict[str, Any]:
        """Convert Profile to dictionary"""
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'expected_sla': self.expected_sla,
            'priority': self.priority,
            'links': [link.to_dict() for link in self.links]
        }

    def has_usable_links(self) -> bool:
        """Check if the profile has any usable links"""
        return any(link.is_usable() for link in self.links)

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

    def get_average_sla(self) -> Optional[float]:
        """Calculate average SLA across all usable links"""
        usable_links = self.get_active_links()
        if not usable_links:
            return None
            
        sla_values = [link.get_effective_sla() or 0 for link in usable_links]
        return sum(sla_values) / len(sla_values)