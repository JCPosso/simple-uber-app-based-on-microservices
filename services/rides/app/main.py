from fastapi import FastAPI
from mangum import Mangum
from .api.routes_rides import router as rides_router

root_path = "/rides-api"
app = FastAPI(title="rides-service")

@app.get(root_path)
async def root():
    return {"message": "Rides Services"}

app.include_router(rides_router, prefix=root_path + "/v1")
handler = Mangum(app)
