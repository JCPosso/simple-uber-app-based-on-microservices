from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional

app = FastAPI(title="drivers-service")
db: dict = {}


class DriverCreate(BaseModel):
    name: str
    carModel: Optional[str] = None
    phone: Optional[str] = None

class Location(BaseModel):
    lat: float
    lon: float
    address: Optional[str] = None

@app.get("/api/v1/drivers")
async def list_drivers(status: Optional[str] = None):
    """List all drivers, optionally filtering by status."""
    allowed = ("OFFLINE", "AVAILABLE", "ON_TRIP")
    if status is not None and status not in allowed:
      raise HTTPException(status_code=400, detail="invalid status")
    drivers = list(db.values())
    if status:
      drivers = [d for d in drivers if d.get("status") == status]
    return drivers

@app.post("/api/v1/drivers", status_code=201)
async def create_driver(d: DriverCreate):
    driver_id = str(uuid4())
    driver = {"driverId": driver_id, "name": d.name, "carModel": d.carModel, "phone": d.phone, "status": "OFFLINE"}
    db[driver_id] = driver
    return driver


@app.get("/api/v1/drivers/available")
async def get_available_driver():
    """Return the first driver with status AVAILABLE or 204 if none."""
    for d in db.values():
        if d.get("status") == "AVAILABLE":
            return d
    # No driver available
    raise HTTPException(status_code=204, detail="no drivers available")

@app.get("/api/v1/drivers/{driver_id}")
async def get_driver(driver_id: str):
    driver = db.get(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="driver not found")
    return driver

@app.patch("/api/v1/drivers/{driver_id}/status")
async def patch_status(driver_id: str, body: dict):
    driver = db.get(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="driver not found")
    status = body.get("status")
    if status not in ("OFFLINE", "AVAILABLE", "ON_TRIP"):
        raise HTTPException(status_code=400, detail="invalid status")
    driver["status"] = status
    return driver


@app.post("/api/v1/drivers/{driver_id}/location")
async def update_location(driver_id: str, loc: Location):
    driver = db.get(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="driver not found")
    driver["location"] = loc.dict()
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}
