from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from sla_data import SLAData

@dataclass
class Link:
    """Represents a routing link with its properties"""
    link_id: str
    operator: str
    mnc: str
    routing_priority: int
    is_active: bool
    last_used: datetime
    sla_data: Optional[SLAData] = None

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

    def get_effective_sla(self) -> Optional[float]:
        """Get the effective SLA for this link"""
        return self.sla_data.get_best_sla() if self.sla_data else None

    def is_usable(self) -> bool:
        """Check if the link is usable based on active status and SLA"""
        return (
            self.is_active and
            self.get_effective_sla() is not None and
            self.get_effective_sla() > 0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Link to dictionary"""
        return {
            'link_id': self.link_id,
            'operator': self.operator,
            'mnc': self.mnc,
            'routing_priority': self.routing_priority,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat(),
            'sla_data': self.sla_data.to_dict() if self.sla_data else None
        }

    def meets_sla_requirement(self, required_sla: float) -> bool:
        """Check if the link meets the required SLA"""
        effective_sla = self.get_effective_sla()
        return (
            effective_sla is not None and
            effective_sla >= required_sla and
            self.is_usable()
        )