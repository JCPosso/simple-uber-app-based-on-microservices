from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class Location(BaseModel):
    lat: float
    lon: float
    address: Optional[str] = None


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class User(UserCreate):
    userId: str = Field(..., alias="userId")
    createdAt: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")


class Driver(BaseModel):
    driverId: str = Field(..., alias="driverId")
    name: str
    carModel: Optional[str] = None
    status: str = "OFFLINE"  # OFFLINE|AVAILABLE|ON_TRIP
    location: Optional[Location] = None
    lastSeen: Optional[datetime] = None


class RideCreate(BaseModel):
    riderId: str
    pickup: Location
    dropoff: Location
    paymentMethodId: Optional[str] = None


class Ride(RideCreate):
    rideId: str = Field(..., alias="rideId")
    driverId: Optional[str] = Field(None, alias="driverId")
    status: str = "REQUESTED"
    fare: Optional[float] = None
    requestedAt: datetime = Field(default_factory=datetime.utcnow, alias="requestedAt")
    updatedAt: Optional[datetime] = Field(None, alias="updatedAt")


class Payment(BaseModel):
    paymentId: str = Field(..., alias="paymentId")
    rideId: str = Field(..., alias="rideId")
    amount: float
    method: str
    status: str = "PENDING"
    processedAt: Optional[datetime] = None
