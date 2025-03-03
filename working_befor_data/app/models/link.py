from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

@dataclass(eq=True, frozen=True)
class Link:
    """Represents a routing link with its properties"""
    link_id: str
    operator: str
    mnc: str
    price: float = 0.0
    average_sla: float = 0.0
    price_history: List[Dict[str, Any]] = field(default_factory=list, hash=False, compare=False)
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Link':
        """Create a Link instance from API data"""
        # Calculate average SLA from available metrics
        sla_values = [
            data.get('sla_dd', 0),
            data.get('sla_tested', 0),
            data.get('sla_assumed', 0)
        ]
        sla_values = [v for v in sla_values if v is not None and v > 0]
        average_sla = sum(sla_values) / len(sla_values) if sla_values else 0
        
        # Get price and price history
        price = data.get('price', 0.0)
        price_history = []
        
        # Add current price to history if available
        if price > 0:
            price_history.append({
                'price': price,
                'timestamp': data.get('last_updated', datetime.now().isoformat()),
                'type': 'initial'
            })
        
        return cls(
            link_id=data['link_id'],
            operator=data['operator'],
            mnc=data['mnc'],
            price=float(price),
            average_sla=average_sla,
            price_history=price_history
        )
    
    def to_optimizer_format(self) -> Dict[str, float]:
        """Convert link data to format needed by optimizer"""
        return {
            "SLA": self.average_sla / 100.0,  # Convert to decimal
            "Price": self.price
        }
    
    def meets_sla_requirement(self, required_sla: float) -> bool:
        """Check if the link meets the required SLA"""
        return self.average_sla >= required_sla
    
    def with_updated_price(self, new_price: float, old_price: Optional[float] = None) -> 'Link':
        """Create a new Link instance with updated price"""
        new_history = []
        
        # Store the old price first
        if old_price is not None:
            new_history.append({
                'price': old_price,
                'timestamp': datetime.now().isoformat(),
                'type': 'initial'
            })
        
        # Add new price to history
        new_history.append({
            'price': new_price,
            'timestamp': datetime.now().isoformat(),
            'type': 'update'
        })
        
        return Link(
            link_id=self.link_id,
            operator=self.operator,
            mnc=self.mnc,
            price=new_price,
            average_sla=self.average_sla,
            price_history=new_history
        )
    
    def get_price_change_percentage(self) -> Optional[float]:
        """Calculate price change percentage from last two prices"""
        if len(self.price_history) >= 2:
            current = self.price_history[-1]['price']
            previous = self.price_history[-2]['price']
            if previous > 0:
                return ((current - previous) / previous) * 100
        return None

    def get_previous_price(self) -> float:
        """Get the previous price from history"""
        if self.price_history:
            for entry in reversed(self.price_history):
                if entry['type'] == 'initial':
                    return entry['price']
        return self.price

    def get_current_price(self) -> float:
        """Get the current price"""
        return self.price

    def get_price_at_index(self, index: int) -> Optional[float]:
        """Get price at specific index in history"""
        if 0 <= index < len(self.price_history):
            return self.price_history[index]['price']
        return None
    
    @staticmethod
    def extract_all_links(profiles: List['Profile']) -> List['Link']:
        """Extract all unique links from a list of profiles"""
        unique_links: Set[Link] = set()
        for profile in profiles:
            unique_links.update(profile.links)
        return sorted(unique_links, key=lambda x: x.mnc)
    
    @staticmethod
    def filter_by_mnc(links: List['Link'], mnc: str) -> List['Link']:
        """Filter links by MNC"""
        return [link for link in links if link.mnc == mnc]
    
    @staticmethod
    def get_links_with_price_changes(links: List['Link']) -> List['Link']:
        """Get all links that have price changes in their history"""
        return [link for link in links if len(link.price_history) > 1]