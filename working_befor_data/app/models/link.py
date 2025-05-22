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