from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass(eq=True, frozen=True)
class Link:
    """Represents a routing link with its properties"""
    link: str  # Link ID
    provider: str
    buy_price: float
    sla_dd: float = 0.0
    tier: int = 1
    traffic: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Tier SLA mapping
    TIER_SLA_MAP = {
        1: 95.0,  # Tier 1 requires 95% SLA
        2: 85.0,  # Tier 2 requires 85% SLA
        3: 75.0   # Tier 3 requires 75% SLA
    }
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Link':
        """Create a Link instance from API data"""
        try:
            # Validate required fields
            required_fields = ['link', 'provider', 'buy_price']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Extract and validate required fields
            try:
                link_id = str(data['link'])
                provider = str(data['provider'])
                buy_price = float(data['buy_price'])
                if buy_price < 0:
                    raise ValueError("buy_price cannot be negative")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value in required fields: {str(e)}")
            
            # Extract and validate optional fields
            try:
                sla_dd = float(data.get('sla_dd', 0.0))
                if not 0 <= sla_dd <= 100:
                    raise ValueError("sla_dd must be between 0 and 100")
                
                tier = int(data.get('tier', 1))
                if tier < 1:
                    raise ValueError("tier must be positive")
                
                traffic = float(data.get('traffic', 0.0))
                if not 0 <= traffic <= 100:
                    raise ValueError("traffic must be between 0 and 100")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value in optional fields: {str(e)}")
            
            # Parse last_updated timestamp
            try:
                last_updated = datetime.fromisoformat(data['last_updated'])
            except (KeyError, ValueError):
                last_updated = datetime.now()
            
            return cls(
                link=link_id,
                provider=provider,
                buy_price=buy_price,
                sla_dd=sla_dd,
                tier=tier,
                traffic=traffic,
                last_updated=last_updated
            )
        except Exception as e:
            raise ValueError(f"Error creating Link from data: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert link data to dictionary format"""
        return {
            'link': self.link,
            'provider': self.provider,
            'buy_price': self.buy_price,
            'sla_dd': self.sla_dd,
            'tier': self.tier,
            'traffic': self.traffic,
            'last_updated': self.last_updated.isoformat()
        }
    
    def to_optimizer_format(self) -> Dict[str, Any]:
        """Convert link data to optimizer-friendly format"""
        return {
            'link': self.link,
            'provider': self.provider,
            'Price': self.buy_price,
            'SLA': self.sla_dd / 100.0,  # Convert to decimal
            'Tier': self.tier,
            'TierSLA': self.TIER_SLA_MAP.get(self.tier, 75.0) / 100.0  # Convert to decimal
        }
    
    def meets_sla_requirement(self, required_sla: float) -> bool:
        """Check if link meets SLA requirement"""
        return self.sla_dd >= required_sla
    
    def calculate_cost_for_traffic(self, traffic_percentage: float, override_price: Optional[float] = None) -> float:
        """Calculate cost for given traffic percentage"""
        price = override_price if override_price is not None else self.buy_price
        return (traffic_percentage / 100.0) * price
    
    def format_display_info(self, traffic_percentage: float, override_price: Optional[float] = None) -> Dict[str, Any]:
        """Format link info for display"""
        price = override_price if override_price is not None else self.buy_price
        return {
            'link': self.link,
            'provider': self.provider,
            'traffic': traffic_percentage,
            'sla': self.sla_dd,
            'tier': self.tier,
            'price': price
        }
    
    def with_updated_price(self, new_price: float, old_price: Optional[float] = None) -> 'Link':
        """Create a new Link instance with updated price"""
        if old_price is not None and self.buy_price != old_price:
            raise ValueError(f"Current price {self.buy_price} does not match old price {old_price}")
        return Link(
            link=self.link,
            provider=self.provider,
            buy_price=new_price,
            sla_dd=self.sla_dd,
            tier=self.tier,
            traffic=self.traffic,
            last_updated=datetime.now()
        )