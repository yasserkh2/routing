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
    
    def __post_init__(self):
        """Initialize a dictionary for fast link lookups."""
        self.link_dict = {link.link: link for link in self.links}
    
    def get_link_by_id(self, link_name: str) -> Optional[Link]:
        """Get a link by its name using a dictionary lookup."""
        return self.link_dict.get(link_name)
    
    def add_link(self, link: Link) -> None:
        """Add a new link to the profile"""
        if link.link not in self.link_dict:
            self.links.append(link)
            self.link_dict[link.link] = link
    
    def remove_link(self, link_name: str) -> bool:
        """Remove a link from the profile by its name"""
        if link_name in self.link_dict:
            self.links = [link for link in self.links if link.link != link_name]
            del self.link_dict[link_name]
            return True
        return False

    def clone(self) -> 'Profile':
        """Create a copy of the profile"""
        cloned = Profile(
            profile_id=self.profile_id,
            name=self.name,
            expected_sla=self.expected_sla,
            links=[link.copy() for link in self.links]
        )
        # __post_init__ will automatically create link_dict
        return cloned
