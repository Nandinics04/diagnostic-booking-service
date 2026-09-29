from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from  app.database import get_db

router=APIRouter()

@router.get("/")
def read_root():
    return {"message": "Diagnostic booking API"}


@router.get("/health/db")
def check_database(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}