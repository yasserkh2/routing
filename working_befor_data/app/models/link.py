from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

@dataclass(eq=True, frozen=True)
class Link:
    """Represents a routing link with its properties"""
    link: str
    operator: str
    mnc: str
    price: float = 0.0
    sla_dd: float = 0.0
    sla_tested: float = 0.0
    sla_assumed: float = 0.0
    average_sla: float = 0.0
    price_history: List[Dict[str, Any]] = field(default_factory=list, hash=False, compare=False)
    sla_history: List[Dict[str, Any]] = field(default_factory=list, hash=False, compare=False)
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Link':
        """Create a Link instance from API data"""
        # Get individual SLA values and validate them
        sla_dd = cls._validate_sla_value(data.get('sla_dd'), 'DD')
        sla_tested = cls._validate_sla_value(data.get('sla_tested'), 'Tested')
        sla_assumed = cls._validate_sla_value(data.get('sla_assumed'), 'Assumed')
        
        # Calculate weighted average SLA using the same weights as other methods
        # Convert None values to 0 and adjust weights accordingly
        weights_sum = 0
        weighted_sum = 0
        
        if sla_dd is not None and sla_dd > 0:
            weighted_sum += sla_dd * 0.4
            weights_sum += 0.4
            
        if sla_tested is not None and sla_tested > 0:
            weighted_sum += sla_tested * 0.35
            weights_sum += 0.35
            
        if sla_assumed is not None and sla_assumed > 0:
            weighted_sum += sla_assumed * 0.25
            weights_sum += 0.25
        
        average_sla = weighted_sum / weights_sum if weights_sum > 0 else 0
        
        # Get price and price history
        price = data.get('price', 0.0)
        price_history = []
        sla_history = []
        
        # Add current price to history if available
        if price > 0:
            price_history.append({
                'price': price,
                'timestamp': data.get('last_updated', datetime.now().isoformat()),
                'type': 'initial'
            })
        
        # Add current SLA values to history
        timestamp = data.get('last_updated', datetime.now().isoformat())
        sla_history.append({
            'sla_dd': sla_dd,
            'sla_tested': sla_tested,
            'sla_assumed': sla_assumed,
            'timestamp': timestamp,
            'type': 'initial'
        })
        
        return cls(
            link=data['link'],
            operator=data['operator'],
            mnc=data['mnc'],
            price=float(price),
            sla_dd=sla_dd,
            sla_tested=sla_tested,
            sla_assumed=sla_assumed,
            average_sla=average_sla,
            price_history=price_history,
            sla_history=sla_history
        )
    
    def to_optimizer_format(self) -> Dict[str, float]:
        """Convert link data to format needed by optimizer"""
        # Calculate weighted SLA using same approach as other methods
        weights_sum = 0
        weighted_sum = 0
        
        if self.sla_dd > 0:
            weighted_sum += self.sla_dd * 0.4
            weights_sum += 0.4
            
        if self.sla_tested > 0:
            weighted_sum += self.sla_tested * 0.35
            weights_sum += 0.35
            
        if self.sla_assumed > 0:
            weighted_sum += self.sla_assumed * 0.25
            weights_sum += 0.25
        
        weighted_sla = (weighted_sum / weights_sum if weights_sum > 0 else 0) / 100.0  # Convert to decimal for optimizer
        
        return {
            "SLA": weighted_sla,
            "Price": self.get_current_price()
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
            link=self.link,
            operator=self.operator,
            mnc=self.mnc,
            price=new_price,
            sla_dd=self.sla_dd,
            sla_tested=self.sla_tested,
            sla_assumed=self.sla_assumed,
            average_sla=self.average_sla,
            price_history=new_history,
            sla_history=self.sla_history
        )

    @staticmethod
    def _validate_sla_value(sla: Optional[float], sla_type: str) -> float:
        """Validate SLA value is within acceptable range"""
        if sla is None:
            return 0.0
        if not isinstance(sla, (int, float)):
            raise ValueError(f"{sla_type} SLA must be a number")
        if not 0 <= sla <= 100:
            raise ValueError(f"{sla_type} SLA must be between 0 and 100")
        return float(sla)

    def update_sla(self, changed_sla: Dict[str, Dict[str, float]]) -> 'Link':
        """Update SLA values and return a new Link instance"""
        # Get new SLA values, keeping existing values if not changed
        new_sla_dd = self.sla_dd
        new_sla_tested = self.sla_tested
        new_sla_assumed = self.sla_assumed

        # Update only the changed SLA values with validation
        if 'DD' in changed_sla:
            new_value = changed_sla['DD'].get('new')
            if new_value is not None:
                new_sla_dd = self._validate_sla_value(new_value, 'DD')
        
        if 'Tested' in changed_sla:
            new_value = changed_sla['Tested'].get('new')
            if new_value is not None:
                new_sla_tested = self._validate_sla_value(new_value, 'Tested')
        
        if 'Assumed' in changed_sla:
            new_value = changed_sla['Assumed'].get('new')
            if new_value is not None:
                new_sla_assumed = self._validate_sla_value(new_value, 'Assumed')
        
        # Calculate weighted average SLA using the same weights as to_optimizer_format
        # Handle None or 0 values by adjusting weights
        weights_sum = 0
        weighted_sum = 0
        
        if new_sla_dd > 0:
            weighted_sum += new_sla_dd * 0.4
            weights_sum += 0.4
            
        if new_sla_tested > 0:
            weighted_sum += new_sla_tested * 0.35
            weights_sum += 0.35
            
        if new_sla_assumed > 0:
            weighted_sum += new_sla_assumed * 0.25
            weights_sum += 0.25
        
        new_average_sla = weighted_sum / weights_sum if weights_sum > 0 else 0

        # Create new history entry
        new_history = list(self.sla_history)
        new_history.append({
            'sla_dd': new_sla_dd,
            'sla_tested': new_sla_tested,
            'sla_assumed': new_sla_assumed,
            'timestamp': datetime.now().isoformat(),
            'type': 'update'
        })

        # Create new Link instance with updated SLA values
        return Link(
            link=self.link,
            operator=self.operator,
            mnc=self.mnc,
            price=self.price,
            sla_dd=new_sla_dd,
            sla_tested=new_sla_tested,
            sla_assumed=new_sla_assumed,
            average_sla=new_average_sla,
            price_history=self.price_history,
            sla_history=new_history
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
    def filter_by_operator(links: List['Link'], operator: str) -> List['Link']:
        """Filter links by operator"""
        return [link for link in links if link.operator == operator]
    
    @staticmethod
    def get_links_with_price_changes(links: List['Link']) -> List['Link']:
        """Get all links that have price changes in their history"""
        return [link for link in links if len(link.price_history) > 1]

    @staticmethod
    def calculate_average_sla(links: List['Link']) -> float:
        """Calculate average SLA across all links"""
        if not links:
            return 0.0
        total_sla = sum(link.average_sla for link in links)
        return total_sla / len(links)

    def format_display_info(self, traffic_percentage: float, override_price: Optional[float] = None) -> Dict[str, Any]:
        """Format link information for display"""
        return {
            'link': self.link,
            'traffic': traffic_percentage,
            'sla': self.average_sla,
            'price': override_price if override_price is not None else self.price
        }

    def calculate_cost_for_traffic(self, traffic_percentage: float, override_price: Optional[float] = None) -> float:
        """Calculate cost for given traffic percentage"""
        traffic_ratio = traffic_percentage / 100.0
        price = override_price if override_price is not None else self.price
        return traffic_ratio * price

    @staticmethod
    def find_by_id(links: List['Link'], link_name: str) -> Optional['Link']:
        """Find a link by its name"""
        return next((link for link in links if link.link == link_name), None)

    def copy(self) -> 'Link':
        """Create a copy of the link instance"""
        return Link(
            link=self.link,
            operator=self.operator,
            mnc=self.mnc,
            price=self.price,
            sla_dd=self.sla_dd,
            sla_tested=self.sla_tested,
            sla_assumed=self.sla_assumed,
            average_sla=self.average_sla,
            price_history=list(self.price_history),
            sla_history=list(self.sla_history)
        )