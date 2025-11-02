from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional

app = FastAPI(title="payments-service")
db: dict = {}


class PaymentRequest(BaseModel):
    rideId: str
    amount: float
    method: str


@app.post("/api/v1/payments", status_code=201)
async def create_payment(p: PaymentRequest):
    payment_id = str(uuid4())
    payment = {"paymentId": payment_id, "rideId": p.rideId, "amount": p.amount, "method": p.method, "status": "PENDING"}
    db[payment_id] = payment
    # In a real service would call payment gateway and update status
    return payment


@app.get("/api/v1/payments/{payment_id}")
async def get_payment(payment_id: str):
    pay = db.get(payment_id)
    if not pay:
        raise HTTPException(status_code=404, detail="payment not found")
    return pay


@app.post("/api/v1/payments/{payment_id}/refund")
async def refund(payment_id: str, body: Optional[dict] = None):
    pay = db.get(payment_id)
    if not pay:
        raise HTTPException(status_code=404, detail="payment not found")
    pay["status"] = "REFUND_REQUESTED"
    return {"ok": True}


@app.post("/api/v1/payments/webhook")
async def webhook(body: dict):
    # placeholder for gateway callbacks
    return {"received": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
