from pydantic import BaseModel
from typing import Optional

class Location(BaseModel):
    lat: float
    lon: float
    address: Optional[str] = None

class RideCreate(BaseModel):
    riderId: str
    pickup: Location
    dropoff: Location
    paymentMethodId: Optional[str] = None
