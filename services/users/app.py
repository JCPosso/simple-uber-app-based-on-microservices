from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI(title="users-service")
db: dict = {}


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None


@app.post("/api/v1/users")
async def create_user(u: UserCreate):
    user_id = str(uuid4())
    user = {"userId": user_id, "name": u.name, "email": u.email, "phone": u.phone}
    db[user_id] = user
    return user


@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    user = db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@app.get("/health")
async def health():
    return {"status": "ok"}
