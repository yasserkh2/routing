from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass(frozen=True)
class SLAData:
    """SLA data for a link"""
    average_sla: float
    last_updated: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SLAData':
        """Create an SLAData instance from a dictionary"""
        return cls(
            average_sla=data['average_sla'],
            last_updated=datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert SLAData to dictionary"""
        return {
            'average_sla': self.average_sla,
            'last_updated': self.last_updated.isoformat()
        }