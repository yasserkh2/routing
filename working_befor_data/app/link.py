from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from sla_data import SLAData

@dataclass(eq=True, frozen=True)
class Link:
    """Represents a routing link with its properties"""
    link_id: str
    operator: str
    mnc: str
    routing_priority: int
    is_active: bool
    last_used: datetime
    sla_data: Optional[SLAData] = None
    price: float = 0.0
    average_sla: float = field(init=False)
    
    def __post_init__(self):
        """Calculate and store average SLA after initialization"""
        # Use object.__setattr__ because the class is frozen
        object.__setattr__(self, 'average_sla',
            self.sla_data.average_sla if self.sla_data else 0.0)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        """Create a Link instance from a dictionary"""
        # Handle different data formats from different APIs
        if 'sla_data' in data:
            sla_data = SLAData.from_dict(data['sla_data'])
        else:
            sla_data = None

        return cls(
            link_id=data['link_id'],
            operator=data['operator'],
            mnc=data['mnc'],
            routing_priority=data.get('routing_priority', 0),
            is_active=data.get('is_active', True),
            last_used=datetime.fromisoformat(data['last_used'].replace('Z', '+00:00')),
            sla_data=sla_data
        )

    def is_usable(self) -> bool:
        """Check if the link is usable based on active status and average SLA"""
        return self.is_active and self.average_sla > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert Link to dictionary"""
        return {
            'link_id': self.link_id,
            'operator': self.operator,
            'mnc': self.mnc,
            'routing_priority': self.routing_priority,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat(),
            'average_sla': self.average_sla
        }

    def meets_sla_requirement(self, required_sla: float) -> bool:
        """Check if the link meets the required SLA"""
        return self.is_usable() and self.average_sla >= required_sla

    @staticmethod
    def extract_all_links(profiles: List['Profile']) -> List['Link']:
        """
        Extract all unique links from a list of profiles.
        
        Args:
            profiles: List of Profile objects
            
        Returns:
            List of unique Link objects
        """
        # Use set for deduplication since Link is now hashable (frozen=True)
        unique_links: Set[Link] = set()
        for profile in profiles:
            unique_links.update(profile.links)
        return sorted(unique_links, key=lambda x: (x.mnc, x.routing_priority))

    @staticmethod
    def get_links_with_mnc_sla(profiles: List['Profile']) -> List[Dict[str, Any]]:
        """
        Get all unique links with their MNC and SLA information.
        
        Args:
            profiles: List of Profile objects
            
        Returns:
            List of dictionaries containing link information
        """
        unique_links = Link.extract_all_links(profiles)
        return [
            {
                'link_id': link.link_id,
                'mnc': link.mnc,
                'operator': link.operator,
                'sla': link.average_sla,
                'routing_priority': link.routing_priority,
                'is_active': link.is_active,
                'sla_data': {
                    'sla_details': link.sla_data.to_dict() if link.sla_data else None
                }
            }
            for link in unique_links
        ]

    @staticmethod
    def get_links_with_average_sla(profiles: List['Profile']) -> List[Dict[str, Any]]:
        """
        Get all unique links with their average SLA values.
        
        Args:
            profiles: List of Profile objects
            
        Returns:
            List of dictionaries containing link information with average SLA
        """
        unique_links = Link.extract_all_links(profiles)
        return [
            {
                'link_id': link.link_id,
                'operator': link.operator,
                'mnc': link.mnc,
                'average_sla': link.average_sla,
                'routing_priority': link.routing_priority,
                'is_active': link.is_active
            }
            for link in unique_links
        ]

    @staticmethod
    def filter_by_mnc(links: List['Link'], mnc: str) -> List['Link']:
        """
        Filter links by MNC.
        
        Args:
            links: List of Link objects
            mnc: MNC to filter by
            
        Returns:
            List of Link objects matching the MNC
        """
        return sorted(
            [link for link in links if link.mnc == mnc],
            key=lambda x: x.routing_priority
        )

    @staticmethod
    def get_links_by_mnc(profiles: List['Profile'], mnc: str) -> List[Dict[str, Any]]:
        """
        Get all links for a specific MNC with their details.
        
        Args:
            profiles: List of Profile objects
            mnc: MNC to filter by
            
        Returns:
            List of dictionaries containing link information for the specified MNC
        """
        all_links = Link.extract_all_links(profiles)
        filtered_links = Link.filter_by_mnc(all_links, mnc)
        
        return [
            {
                'link_id': link.link_id,
                'operator': link.operator,
                'sla': link.average_sla,
                'routing_priority': link.routing_priority,
                'is_active': link.is_active,
                'last_used': link.last_used.isoformat()
            }
            for link in filtered_links
        ]