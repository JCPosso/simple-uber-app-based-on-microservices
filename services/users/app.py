from fastapi import FastAPI, HTTPException
from uuid import uuid4
from shared_models import UserCreate, User

app = FastAPI(title="users-service")
db: dict = {}


@app.post("/api/v1/users", status_code=201)
async def create_user(u: UserCreate):
    user_id = str(uuid4())
    user = User(userId=user_id, name=u.name, email=u.email, phone=u.phone)
    db[user_id] = user.dict(by_alias=True)
    return db[user_id]


@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: str):
    user = db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@app.get("/health")
async def health():
    return {"status": "ok"}
