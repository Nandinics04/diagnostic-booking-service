from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Centre, DiagnosticTest, User
from app.routers.auth import get_current_user
from app.schemas import CentreCreate, CentreResponse, TestCreate, TestResponse

router=APIRouter(tags=["centres"])

@router.post("/centres", response_model=CentreResponse, status_code=status.HTTP_201_CREATED)
def create_centre(
    body: CentreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre=Centre(name=body.name,location=body.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre

@router.get("/centres", response_model=list[CentreResponse])
def list_centres(db: Session = Depends(get_db)):
    return db.scalars(select(Centre).order_by(Centre.id)).all()

@router.get("/centres/{centre_id}", response_model=CentreResponse)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    centre=db.get(Centre,centre_id)
    if centre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    return centre

@router.post("/centres/{centre_id}/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
def create_test(
    centre_id: int,
    body: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre=db.get(Centre,centre_id)
    if centre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    test=DiagnosticTest(centre_id=centre.id,name=body.name,price=body.price)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test

@router.get("/centres/{centre_id}/tests", response_model=list[TestResponse])
def list_tests(centre_id: int, db: Session = Depends(get_db)):
    centre=db.get(Centre,centre_id)
    if centre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    return db.scalars(
        select(DiagnosticTest)
        .where(DiagnosticTest.centre_id==centre.id)
        .order_by(DiagnosticTest.id)
        ).all()