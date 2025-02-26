from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from profile import Profile
from link import Link

@dataclass
class ProfileManager:
    """Manages all routing profiles and their SLA requirements"""
    profiles: List[Profile] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileManager':
        """Create a ProfileManager instance from a dictionary"""
        profiles = [Profile.from_dict(profile_data) for profile_data in data.get('profiles', [])]
        return cls(profiles=profiles)

    def add_profile(self, profile: Profile) -> None:
        """Add a new profile"""
        if not any(p.profile_id == profile.profile_id for p in self.profiles):
            self.profiles.append(profile)

    def remove_profile(self, profile_id: str) -> bool:
        """Remove a profile by its ID"""
        initial_length = len(self.profiles)
        self.profiles = [p for p in self.profiles if p.profile_id != profile_id]
        return len(self.profiles) < initial_length

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get a profile by its ID"""
        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        return None

    def get_profiles_by_sla(self, min_sla: float) -> List[Profile]:
        """Get all profiles with expected SLA >= min_sla"""
        return [p for p in self.profiles if p.expected_sla >= min_sla]

    def get_profiles_by_priority(self, priority: str) -> List[Profile]:
        """Get all profiles with specified priority"""
        return [p for p in self.profiles if p.priority == priority]

    def get_profiles_using_link(self, link_id: str) -> List[Profile]:
        """Get all profiles that use a specific link"""
        return [
            profile for profile in self.profiles
            if any(link.link_id == link_id for link in profile.links)
        ]

    def get_profiles_by_mnc(self, mnc: str) -> List[Profile]:
        """Get all profiles that have links with specified MNC"""
        return [
            profile for profile in self.profiles
            if any(link.mnc == mnc for link in profile.links)
        ]

    def get_average_sla_by_priority(self) -> Dict[str, float]:
        """Get average expected SLA for each priority level"""
        sla_by_priority: Dict[str, List[float]] = {}
        for profile in self.profiles:
            if profile.priority not in sla_by_priority:
                sla_by_priority[profile.priority] = []
            sla_by_priority[profile.priority].append(profile.expected_sla)

        return {
            priority: sum(slas) / len(slas)
            for priority, slas in sla_by_priority.items()
        }

    def get_sla_summary(self) -> Dict[str, Any]:
        """Get summary of SLA requirements across all profiles"""
        if not self.profiles:
            return {
                'min_sla': 0.0,
                'max_sla': 0.0,
                'avg_sla': 0.0,
                'profiles_count': 0
            }

        sla_values = [p.expected_sla for p in self.profiles]
        return {
            'min_sla': min(sla_values),
            'max_sla': max(sla_values),
            'avg_sla': sum(sla_values) / len(sla_values),
            'profiles_count': len(self.profiles)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert ProfileManager to dictionary"""
        return {
            'profiles': [profile.to_dict() for profile in self.profiles],
            'sla_summary': self.get_sla_summary(),
            'priority_slas': self.get_average_sla_by_priority()
        }

    def update_profile_sla(self, profile_id: str, new_sla: float) -> bool:
        """Update a profile's expected SLA"""
        profile = self.get_profile(profile_id)
        if profile:
            profile.expected_sla = new_sla
            return True
        return False

    def get_profiles_with_usable_links(self) -> List[Profile]:
        """Get all profiles that have usable links"""
        return [p for p in self.profiles if p.has_usable_links()]

    def get_profiles_meeting_sla(self) -> List[Profile]:
        """Get all profiles that have links meeting their SLA requirements"""
        return [
            profile for profile in self.profiles
            if any(link.average_sla >= profile.expected_sla for link in profile.links)
        ]