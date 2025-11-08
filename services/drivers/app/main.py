from fastapi import FastAPI
from mangum import Mangum
from .api.routes_drivers import router as drivers_router

root_path = "/drivers-api"
app = FastAPI(title="drivers-service")

@app.get(root_path)
async def root():
    return {"message": "Drivers Services"}

app.include_router(drivers_router, prefix=root_path + "/v1")
handler = Mangum(app)
