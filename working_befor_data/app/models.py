from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Route(BaseModel):
    """Model for a single route with SLA data"""
    reference_id: str
    product_name: str
    provider_name: str
    name: str
    network_name: str
    mcc: str
    mnc: str
    old_rate: float
    new_rate: float
    margin_percentage: float
    price_change_status: str
    created_on: str
    sla_dd: Optional[float] = None
    sla_tested: Optional[float] = None
    sla_assumed: float

    class Config:
        from_attributes = True

class RoutesResponse(BaseModel):
    """Response model for routes endpoint"""
    count: int
    routes: List[Route]

class Profile(BaseModel):
    """Model for a product profile with SLA coverage"""
    product_name: str
    route_count: int
    average_margin: float
    dd_coverage: float = Field(description="Percentage of routes with Datadog SLA data")
    test_coverage: float = Field(description="Percentage of routes with test SLA data")

class ProfilesResponse(BaseModel):
    """Response model for profiles endpoint"""
    count: int
    profiles: List[Profile]

class ProductSLAData(BaseModel):
    """Model for SLA data grouped by product"""
    routes: List[Route]
    sla_dd_available: int
    sla_tested_available: int
    average_sla_dd: float
    average_sla_tested: float
    sla_assumed: float

class RouteSLAResponse(BaseModel):
    """Response model for route SLA endpoint"""
    mcc: str
    mnc: str
    products: Dict[str, ProductSLAData]

class SLACoverage(BaseModel):
    """Model for SLA coverage statistics"""
    datadog: float
    tested: float
    assumed: float = 100.0

class RoutesSummary(BaseModel):
    """Response model for routes summary endpoint"""
    total_routes: int
    sla_coverage: SLACoverage
    unique_products: int
    unique_networks: int
    timestamp: datetime

class APIInfo(BaseModel):
    """Model for API information"""
    name: str
    version: str
    status: str
    endpoints: Dict[str, str]

class MessageResponse(BaseModel):
    """Model for simple message responses"""
    message: str