from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class SLAData:
    """SLA data for a link from different sources"""
    sla_dd: Optional[float]
    sla_tested: Optional[float]
    sla_assumed: Optional[float]
    last_updated: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SLAData':
        """Create an SLAData instance from a dictionary"""
        return cls(
            sla_dd=data.get('sla_dd'),
            sla_tested=data.get('sla_tested'),
            sla_assumed=data.get('sla_assumed'),
            last_updated=datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))
        )

    def get_best_sla(self) -> Optional[float]:
        """Get the best available SLA value in order of preference"""
        if self.sla_dd is not None:
            return self.sla_dd
        if self.sla_tested is not None:
            return self.sla_tested
        return self.sla_assumed

    def to_dict(self) -> Dict[str, Any]:
        """Convert SLAData to dictionary"""
        return {
            'sla_dd': self.sla_dd,
            'sla_tested': self.sla_tested,
            'sla_assumed': self.sla_assumed,
            'last_updated': self.last_updated.isoformat()
        }