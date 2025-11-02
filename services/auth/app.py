from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="auth-service")


class TokenRequest(BaseModel):
    username: str
    password: str


@app.post("/token")
async def token(req: TokenRequest):
    if not req.username:
        raise HTTPException(status_code=400, detail="username required")
    return {"access_token": f"fake-token-for-{req.username}", "token_type": "bearer"}


@app.get("/health")
async def health():
    return {"status": "ok"}
