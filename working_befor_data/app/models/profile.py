from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from functools import lru_cache

@dataclass
class Profile:
    """Represents a routing profile with its properties"""
    profile_id: str
    name: str
    expected_sla: float = 0.0
    description: str = ""
    sell_price_min: float = 0.0
    sell_price_max: float = 0.0
    profile_avg_cost: float = 0.0
    mcc: str = ""
    mnc: str = ""
    in_use_links: List[str] = field(default_factory=list)  # List of link names only
    alternative_links: List[str] = field(default_factory=list)  # List of link names only
    link_labels: Dict[str, str] = field(default_factory=dict)  # Maps link name to label
    link_status: Dict[str, str] = field(default_factory=dict)  # Maps link name to status
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Profile':
        """Create a Profile instance from API data"""
        try:
            # Validate required fields
            required_fields = ['profile_id', 'name']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Extract in-use link names and their labels/status
            in_use_links = []
            link_labels = {}
            link_status = {}
            
            for link_data in data.get('in_use_links', []):
                if isinstance(link_data, dict) and 'link' in link_data:
                    link_name = link_data['link']
                    in_use_links.append(link_name)
                    
                    # Set status for in-use links
                    link_status[link_name] = "in_use"
                    
                    # Set label for in-use links (use provided label or default)
                    if 'label' in link_data and link_data['label']:
                        link_labels[link_name] = link_data['label']
                    else:
                        link_labels[link_name] = "Active Link"
            
            # Extract alternative link names if present in the profile data
            alternative_links = []
            if 'alternative_links' in data:
                for link_data in data.get('alternative_links', []):
                    if isinstance(link_data, dict) and 'link' in link_data:
                        link_name = link_data['link']
                        alternative_links.append(link_name)
                        
                        # Set status for alternative links
                        link_status[link_name] = "alternative"
                        
                        # Set label for alternative links (use provided label or default)
                        if 'label' in link_data and link_data['label']:
                            link_labels[link_name] = link_data['label']
                        else:
                            link_labels[link_name] = "Alternative Link"
            
            return cls(
                profile_id=str(data['profile_id']),
                name=str(data['name']),
                expected_sla=float(data.get('expected_sla', 0.0)),
                description=str(data.get('description', '')),
                sell_price_min=float(data.get('sell_price_min', 0.0)),
                sell_price_max=float(data.get('sell_price_max', 0.0)),
                profile_avg_cost=float(data.get('profile_avg_cost', 0.0)),
                mcc=str(data.get('mcc', '')),
                mnc=str(data.get('mnc', '')),
                in_use_links=in_use_links,
                alternative_links=alternative_links,
                link_labels=link_labels,
                link_status=link_status
            )
        except Exception as e:
            raise ValueError(f"Error creating Profile from data: {str(e)}")
    
    def get_all_links(self) -> List[str]:
        """Get all link names (both in-use and alternative)"""
        return self.in_use_links + self.alternative_links
    
    def has_link(self, link_name: str) -> bool:
        """Check if profile has a specific link"""
        return link_name in self.in_use_links or link_name in self.alternative_links
    
    def is_link_active(self, link_name: str) -> bool:
        """Check if a link is in the in-use list"""
        return link_name in self.in_use_links
    
    def add_link(self, link_name: str, is_active: bool = False, label: str = None) -> None:
        """Add a new link name to the profile"""
        # Set default label if not provided
        if label is None:
            label = "Active Link" if is_active else "Alternative Link"
        
        # Add link to appropriate list
        if is_active and link_name not in self.in_use_links:
            self.in_use_links.append(link_name)
            self.link_status[link_name] = "in_use"
            # Remove from alternative links if it was there
            if link_name in self.alternative_links:
                self.alternative_links.remove(link_name)
        elif not is_active and link_name not in self.alternative_links:
            self.alternative_links.append(link_name)
            self.link_status[link_name] = "alternative"
            # Remove from in_use links if it was there
            if link_name in self.in_use_links:
                self.in_use_links.remove(link_name)
        
        # Store label
        self.link_labels[link_name] = label
    
    def remove_link(self, link_name: str) -> bool:
        """Remove a link from the profile by its name"""
        removed = False
        if link_name in self.in_use_links:
            self.in_use_links.remove(link_name)
            removed = True
        elif link_name in self.alternative_links:
            self.alternative_links.remove(link_name)
            removed = True
        
        # Clean up label and status if link was removed
        if removed:
            if link_name in self.link_labels:
                del self.link_labels[link_name]
            if link_name in self.link_status:
                del self.link_status[link_name]
        
        return removed

    
    def get_link_label(self, link_name: str) -> str:
        """Get the label for a specific link"""
        return self.link_labels.get(link_name, "")
    
    def get_link_status(self, link_name: str) -> str:
        """Get the status for a specific link"""
        return self.link_status.get(link_name, "")
    
    def set_link_label(self, link_name: str, label: str) -> None:
        """Set the label for a specific link"""
        if self.has_link(link_name):
            self.link_labels[link_name] = label
    
    def set_link_status(self, link_name: str, status: str) -> None:
        """Set the status for a specific link"""
        if not self.has_link(link_name):
            return
            
        old_status = self.get_link_status(link_name)
        if old_status == status:
            return
            
        # Update status in dictionary
        self.link_status[link_name] = status
        
        # Move link between lists based on new status
        if status == "in_use" and link_name in self.alternative_links:
            self.alternative_links.remove(link_name)
            if link_name not in self.in_use_links:
                self.in_use_links.append(link_name)
        elif status == "alternative" and link_name in self.in_use_links:
            self.in_use_links.remove(link_name)
            if link_name not in self.alternative_links:
                self.alternative_links.append(link_name)
    
    def get_links_with_info(self) -> List[Dict[str, Any]]:
        """Get all links with their labels and status information"""
        result = []
        for link_name in self.get_all_links():
            result.append({
                'link': link_name,
                'label': self.get_link_label(link_name),
                'status': self.get_link_status(link_name),
                'is_active': link_name in self.in_use_links
            })
        return result
    
    def clone(self) -> 'Profile':
        """Create a copy of the profile"""
        return Profile(
            profile_id=self.profile_id,
            name=self.name,
            expected_sla=self.expected_sla,
            description=self.description,
            sell_price_min=self.sell_price_min,
            sell_price_max=self.sell_price_max,
            profile_avg_cost=self.profile_avg_cost,
            mcc=self.mcc,
            mnc=self.mnc,
            in_use_links=list(self.in_use_links),
            alternative_links=list(self.alternative_links),
            link_labels=dict(self.link_labels),
            link_status=dict(self.link_status)
        )
