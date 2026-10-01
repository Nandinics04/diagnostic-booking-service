import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.database import Base,engine
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.centres import router as centres_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router
import app.models


logger = logging.getLogger("eve")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="EVE Diagnostic booking API", lifespan=lifespan)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start=time.perf_counter()
    response=await call_next(request)
    duration_ms=round((time.perf_counter()-start)*100,1)
    logger.info(
        "method=%s, path=%s, status=%s, duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(centres_router)
app.include_router(bookings_router)
app.include_router(payments_router)