from fastapi import FastAPI, HTTPException
from uuid import uuid4

app = FastAPI(title="users-service")
db: dict = {}

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class User(UserCreate):
    userId: str = Field(..., alias="userId")
    createdAt: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")

@app.get("/api/v1/users")
async def list_users():
    return list(db.values())

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
