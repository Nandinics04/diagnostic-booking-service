import os
from pathlib import Path

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
values = dotenv_values(root / ".env")
os.environ["DATABASE_URL"] = values["DATABASE_URL"].rsplit("/", 1)[0] + "/eve_booking_test"
os.environ["JWT_SECRET_KEY"] = values["JWT_SECRET_KEY"]

import pytest
from fastapi.testclient import TestClient

from app.limiter import limiter
from app.database import Base, engine
from main import app

limiter.reset()
@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)