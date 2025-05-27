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
    label: str = ""
    status: str = "alternative"  # "in_use" or "alternative"
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Tier SLA mapping
    TIER_SLA_MAP = {
        "Tier 1 – Prime": 95.0,
        "Tier 2 – High": 90.0,
        "Tier 3 – Med": 80.0,
        "Tier 4 – Low": 70.0,
        "Tier 5 – Unverified": 80.0,
        "Tier 6 – Local": 80.0,
        "Tier 7 – WhatsApp": 80.0,
        "Tier 8 – P2P": 80.0,
        "Tier 9 – Custom Route": None  # no formal SLA; set case-by-case
    }
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Link':
        """Create a Link instance from API data"""
        try:
            # Validate required fields
            required_fields = ['link', 'provider']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Extract and validate required fields
            try:
                link_id = str(data['link'])
                provider = str(data['provider'])
                
                # Check for either 'buy_price' or 'base_buy_price'
                if 'buy_price' in data:
                    buy_price = float(data['buy_price'])
                elif 'base_buy_price' in data:
                    buy_price = float(data['base_buy_price'])
                else:
                    buy_price = 0.0
                    
                if buy_price < 0:
                    raise ValueError("buy_price cannot be negative")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value in required fields: {str(e)}")
            
            # Extract and validate optional fields
            try:
                sla_dd = float(data.get('sla_dd', 0.0))
                if not 0 <= sla_dd <= 100:
                    raise ValueError("sla_dd must be between 0 and 100")
                
                # Handle tier field which could be an integer or a string like "Tier 1 - Prime"
                tier_value = data.get('tier', 1)
                if isinstance(tier_value, int):
                    tier = tier_value
                elif isinstance(tier_value, str):
                    # Extract tier number from string like "Tier 1 - Prime"
                    if tier_value.startswith("Tier "):
                        try:
                            tier = int(tier_value.split(" ")[1])
                        except (ValueError, IndexError):
                            tier = 1
                    else:
                        tier = 1
                else:
                    tier = 1
                
                if tier < 1:
                    tier = 1
                
                traffic = float(data.get('traffic', 0.0))
                if not 0 <= traffic <= 100:
                    raise ValueError("traffic must be between 0 and 100")
                
                # Determine if link is in use based on traffic or explicit status
                status = data.get('status', '')
                if not status:
                    status = "in_use" if traffic > 0 else "alternative"
                
                # Set a default label based on status if not provided
                label = str(data.get('label', ''))
                if not label:
                    if status == "in_use":
                        label = "Active Link"
                    else:
                        label = "Alternative Link"
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
                label=label,
                status=status,
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
            'label': self.label,
            'status': self.status,
            'last_updated': self.last_updated.isoformat()
        }
    
    def get_tier_name(self) -> str:
        """Get the name of the tier based on tier number"""
        tier_names = list(self.TIER_SLA_MAP.keys())
        if 1 <= self.tier <= len(tier_names):
            return tier_names[self.tier - 1]
        return "Unknown Tier"
    
    def get_tier_sla(self) -> float:
        """Get the SLA value for this link's tier"""
        tier_name = self.get_tier_name()
        tier_sla = self.TIER_SLA_MAP.get(tier_name)
        # Return 0 for None or custom tiers without formal SLA
        return tier_sla if tier_sla is not None else 0.0
    
    def calculate_effective_sla(self) -> float:
        """
        Calculate the effective SLA for this link.
        If sla_dd is provided, use it; otherwise use the tier SLA.
        """
        if self.sla_dd > 0:
            return self.sla_dd
        return self.get_tier_sla()
    
    def to_optimizer_format(self) -> Dict[str, Any]:
        """Convert link data to optimizer-friendly format"""
        tier_name = self.get_tier_name()
        tier_sla = self.get_tier_sla()
        
        # Calculate effective SLA (use sla_dd if available, otherwise use tier SLA)
        effective_sla = self.calculate_effective_sla()
        
        return {
            'link': self.link,
            'provider': self.provider,
            'price': self.buy_price,
            'sla': effective_sla / 100.0,  # Convert to decimal
            'tier': self.tier,
            'tier_name': tier_name,
            'tier_sla': tier_sla / 100.0 if tier_sla is not None else 0.0,  # Convert to decimal
            'label': self.label,
            'status': self.status
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
            'price': price,
            'label': self.label,
            'status': self.status
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
            label=self.label,
            status=self.status,
            last_updated=datetime.now()
        )