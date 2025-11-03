from pydantic import BaseModel
from typing import Optional

class DriverCreate(BaseModel):
    name: str
    carModel: Optional[str] = None
    phone: Optional[str] = None

class Location(BaseModel):
    lat: float
    lon: float
    address: Optional[str] = None