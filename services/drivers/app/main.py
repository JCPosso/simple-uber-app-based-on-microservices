from fastapi import FastAPI
from mangum import Mangum
from .api import routes_drivers

app = FastAPI(title="drivers-service")
app.include_router(routes_drivers.router)

handler = Mangum(app)
