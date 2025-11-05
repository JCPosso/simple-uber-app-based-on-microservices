from fastapi import FastAPI
from mangum import Mangum
from .api import routes_rides

app = FastAPI(title="rides-service")
app.include_router(routes_rides.router)

handler = Mangum(app)
