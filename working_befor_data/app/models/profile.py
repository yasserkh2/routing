from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from .link import Link

@dataclass
class Profile:
    """Represents a routing profile with its properties"""
    profile_id: str
    name: str
    expected_sla: float
    priority: str
    links: List[Link]
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any], available_links: List[Link]) -> 'Profile':
        """Create a Profile instance from API data"""
        # Get links assigned to this profile
        profile_links = [
            link for link in available_links 
            if link.link_id in data['links']
        ]
        
        return cls(
            profile_id=data['profile_id'],
            name=data['name'],
            expected_sla=float(data['expected_sla']),
            priority=data['priority'],
            links=profile_links
        )

    @classmethod
    def get_profiles_affected_by_price_change(cls, profiles: List['Profile'], link_id: str) -> List['Profile']:
        """Get all profiles that contain the link with price change"""
        return [
            profile for profile in profiles
            if any(link.link_id == link_id for link in profile.links)
        ]
    
    def update_link_price(self, link_id: str, new_price: float, old_price: Optional[float] = None) -> bool:
        """Update price for a specific link in the profile"""
        for i, link in enumerate(self.links):
            if link.link_id == link_id:
                # Create new Link instance with updated price
                updated_link = Link(
                    link_id=link.link_id,
                    operator=link.operator,
                    mnc=link.mnc,
                    price=new_price,
                    average_sla=link.average_sla,
                    price_history=[
                        {'price': old_price or link.price, 'timestamp': datetime.now().isoformat(), 'type': 'initial'},
                        {'price': new_price, 'timestamp': datetime.now().isoformat(), 'type': 'update'}
                    ]
                )
                # Replace old link with updated one
                self.links[i] = updated_link
                return True
        return False
    
    def to_optimizer_format(self) -> Dict[str, Any]:
        """Convert profile data to format needed by optimizer"""
        links_data = {}
        for link in self.links:
            if link.average_sla > 0:
                links_data[link.link_id] = link.to_optimizer_format()
                
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'expected_sla': self.expected_sla,
            'links': links_data
        }
    
    def get_active_links(self) -> List[Link]:
        """Get all active links that meet the profile's SLA requirement"""
        return [
            link for link in self.links 
            if link.meets_sla_requirement(self.expected_sla)
        ]
    
    def get_link_by_id(self, link_id: str) -> Optional[Link]:
        """Get a link by its ID"""
        for link in self.links:
            if link.link_id == link_id:
                return link
        return None
    
    def add_link(self, link: Link) -> None:
        """Add a new link to the profile"""
        if not any(existing.link_id == link.link_id for existing in self.links):
            self.links.append(link)
    
    def remove_link(self, link_id: str) -> bool:
        """Remove a link from the profile by its ID"""
        initial_length = len(self.links)
        self.links = [link for link in self.links if link.link_id != link_id]
        return len(self.links) < initial_length
    
    def get_links_by_operator(self, operator: str) -> List[Link]:
        """Get all links for a specific operator"""
        return [link for link in self.links if link.operator == operator]
    
    def get_links_by_mnc(self, mnc: str) -> List[Link]:
        """Get all links for a specific MNC"""
        return [link for link in self.links if link.mnc == mnc]
    
    def calculate_cost(self, routing_plan: Dict[str, Any], use_previous_price: bool = False) -> float:
        """Calculate total cost based on a routing plan"""
        total_cost = 0.0
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.get_link_by_id(route['link_id'])
                if link:
                    # Convert percentage to decimal and multiply by price
                    price = link.get_previous_price() if use_previous_price else link.get_current_price()
                    if price is not None:
                        total_cost += (route['percentage'] / 100.0) * price
        return total_cost
    
    def calculate_cost_impact(self, before_plan: Dict[str, Any], after_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost impact between two routing plans"""
        before_cost = self.calculate_cost(before_plan)
        after_cost = self.calculate_cost(after_plan)
        cost_change = after_cost - before_cost
        cost_change_pct = (cost_change / before_cost) * 100 if before_cost > 0 else 0
        
        return {
            'before_cost': before_cost,
            'after_cost': after_cost,
            'savings': abs(cost_change),
            'percentage': abs(cost_change_pct)
        }

    def calculate_achieved_sla(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate achieved SLA based on routing plan"""
        achieved_sla = 0.0
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.get_link_by_id(route['link_id'])
                if link:
                    achieved_sla += (route['percentage'] / 100.0) * (link.average_sla / 100.0)
        return achieved_sla * 100  # Convert back to percentage

    def get_optimization_stats(self, routing_plan: Dict[str, Any], use_previous_price: bool = False) -> Dict[str, Any]:
        """Get optimization statistics for a routing plan"""
        total_cost = self.calculate_cost(routing_plan, use_previous_price)
        achieved_sla = self.calculate_achieved_sla(routing_plan)
        active_links = len([route for route in routing_plan['routes'] if route['percentage'] > 0.001])

        return {
            'total_cost': total_cost,
            'links_used': active_links,
            'achieved_sla': achieved_sla,
            'expected_sla': self.expected_sla
        }

    def format_routing_display(self, routing_plan: Dict[str, Any], use_previous_price: bool = False) -> List[Dict[str, Any]]:
        """Format routing plan for display"""
        display_routes = []
        for route in routing_plan['routes']:
            if route['percentage'] > 0:
                link = self.get_link_by_id(route['link_id'])
                if link:
                    # Use the current price from the link
                    price = link.price
                    display_routes.append({
                        'link_id': link.link_id,
                        'traffic': route['percentage'],
                        'sla': link.average_sla,
                        'price': price
                    })
        return display_routes

    def get_link_price(self, link_id: str, use_previous: bool = False) -> Optional[float]:
        """Get link price (current or previous)"""
        link = self.get_link_by_id(link_id)
        if link:
            return link.get_previous_price() if use_previous else link.get_current_price()
        return None

    def calculate_total_traffic(self, routing_plan: Dict[str, Any]) -> float:
        """Calculate total traffic allocation"""
        return sum(route['percentage'] for route in routing_plan['routes'])