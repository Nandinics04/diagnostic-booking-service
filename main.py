from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import Base,engine
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
import app.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="EVE Diagnostic booking API", lifespan=lifespan)

app.include_router(health_router)
app.include_router(auth_router)