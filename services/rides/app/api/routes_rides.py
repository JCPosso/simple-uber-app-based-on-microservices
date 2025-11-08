from fastapi import APIRouter, HTTPException
from uuid import uuid4
import os
import asyncio
from datetime import datetime
import json
from pydantic import BaseModel
from typing import Optional
from ..models.ride import RideCreate, Location

router = APIRouter(prefix="/rides", tags=["rides"])
db = {}

try:
    import aio_pika
except Exception:
    aio_pika = None

@router.get("")
async def list_rides():
    """Return all rides as a list."""
    return list(db.values())

@router.post("", status_code=201)
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
        try:
            await publish_ride_requested(rmq, ride)
        except Exception as e:
            print(f"[ERROR] Failed to publish ride_requested: {e}")

    return ride


async def publish_ride_requested(rabbit_url, ride):
    """Publica un evento `ride.requested` al exchange `ride_events` con metadata.

    Mensaje JSON con campos: type, rideId, riderId, pickup, dropoff, metadata
    """
    try:
        conn = await aio_pika.connect_robust(rabbit_url)
        channel = await conn.channel()
        exchange = await channel.declare_exchange("ride_events", aio_pika.ExchangeType.TOPIC, durable=True)
        payload = {
            "type": "ride.requested",
            "rideId": ride.get("rideId"),
            "riderId": ride.get("riderId"),
            "pickup": ride.get("pickup"),
            "dropoff": ride.get("dropoff"),
            "metadata": {
                "correlation_id": str(uuid4()),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }
        msg = aio_pika.Message(body=json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
        await exchange.publish(msg, routing_key="ride.requested")
        await conn.close()
    except Exception as exc:
        print("[rides] publish_ride_requested error:", exc)

@router.patch("/{ride_id}/assign")
async def assign_driver(ride_id: str, body: dict):
    """Endpoint para que el matching worker asigne un driver.

    body: { "driverId": "..." }
    """
    ride = db.get(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="ride not found")
    driver_id = body.get("driverId")
    if not driver_id:
        raise HTTPException(status_code=400, detail="driverId required")
    ride["driverId"] = driver_id
    ride["status"] = "MATCHED"
    return ride

@router.get("/{ride_id}")
async def get_ride(ride_id: str):
    ride = db.get(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="ride not found")
    return ride