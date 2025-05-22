from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set

@dataclass
class Profile:
    """Represents a routing profile with its properties"""
    profile_id: str
    name: str
    expected_sla: float
    description: str
    sell_price_min: float
    sell_price_max: float
    profile_avg_cost: float
    mcc: str
    mnc: str
    in_use_links: List[str]  # List of link names only
    alternative_links: List[str]  # List of link names only
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Profile':
        """Create a Profile instance from API data"""
        try:
            # Validate required fields
            required_fields = [
                'profile_id', 'name', 'expected_sla', 'description',
                'sell_price_min', 'sell_price_max', 'profile_avg_cost',
                'mcc', 'mnc'
            ]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Extract only link names from in_use_links
            in_use_links = [
                link_data['link']
                for link_data in data.get('in_use_links', [])
                if isinstance(link_data, dict) and 'link' in link_data
            ]
            
            # Extract only link names from alternative_links
            alternative_links = [
                link_data['link']
                for link_data in data.get('alternative_links', [])
                if isinstance(link_data, dict) and 'link' in link_data
            ]
        
            # Convert and validate numeric fields
            try:
                expected_sla = float(data['expected_sla'])
                if not 0 <= expected_sla <= 100:
                    raise ValueError("expected_sla must be between 0 and 100")
                
                sell_price_min = float(data['sell_price_min'])
                if sell_price_min < 0:
                    raise ValueError("sell_price_min cannot be negative")
                
                sell_price_max = float(data['sell_price_max'])
                if sell_price_max < sell_price_min:
                    raise ValueError("sell_price_max cannot be less than sell_price_min")
                
                profile_avg_cost = float(data['profile_avg_cost'])
                if profile_avg_cost < 0:
                    raise ValueError("profile_avg_cost cannot be negative")
                
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid numeric value in profile data: {str(e)}")
            
            return cls(
                profile_id=str(data['profile_id']),
                name=str(data['name']),
                expected_sla=expected_sla,
                description=str(data['description']),
                sell_price_min=sell_price_min,
                sell_price_max=sell_price_max,
                profile_avg_cost=profile_avg_cost,
                mcc=str(data['mcc']),
                mnc=str(data['mnc']),
                in_use_links=in_use_links,
                alternative_links=alternative_links
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
    
    def add_link(self, link_name: str, is_active: bool = False) -> None:
        """Add a new link name to the profile"""
        if is_active and link_name not in self.in_use_links:
            self.in_use_links.append(link_name)
        elif not is_active and link_name not in self.alternative_links:
            self.alternative_links.append(link_name)
    
    def remove_link(self, link_name: str) -> bool:
        """Remove a link from the profile by its name"""
        if link_name in self.in_use_links:
            self.in_use_links.remove(link_name)
            return True
        elif link_name in self.alternative_links:
            self.alternative_links.remove(link_name)
            return True
        return False

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
            alternative_links=list(self.alternative_links)
        )
