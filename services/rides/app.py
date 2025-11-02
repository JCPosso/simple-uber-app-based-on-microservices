from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import os
import asyncio

try:
    import aio_pika
except Exception:
    aio_pika = None

app = FastAPI(title="rides-service")
db: dict = {}


class Location(BaseModel):
    lat: float
    lon: float


class RideCreate(BaseModel):
    riderId: str
    pickup: Location
    dropoff: Location


@app.post("/api/v1/rides")
async def create_ride(r: RideCreate):
    ride_id = str(uuid4())
    ride = {
        "rideId": ride_id,
        "riderId": r.riderId,
        "pickup": r.pickup.dict(),
        "dropoff": r.dropoff.dict(),
        "status": "REQUESTED",
    }
    db[ride_id] = ride
    rmq = os.getenv("RABBITMQ_URL")
    if rmq and aio_pika:
        asyncio.create_task(publish_ride_requested(rmq, ride))
    return ride


async def publish_ride_requested(rabbit_url, ride):
    try:
        conn = await aio_pika.connect_robust(rabbit_url)
        channel = await conn.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=str(ride).encode()), routing_key="ride.requested"
        )
        await conn.close()
    except Exception:
        pass


@app.get("/api/v1/rides/{ride_id}")
async def get_ride(ride_id: str):
    ride = db.get(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="ride not found")
    return ride


@app.get("/health")
async def health():
    return {"status": "ok"}
