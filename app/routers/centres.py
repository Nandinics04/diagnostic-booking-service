from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select,func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Centre, DiagnosticTest, User
from app.routers.auth import get_current_user
from app.schemas import CentreCreate, CentreResponse, TestCreate, TestResponse, Page
from app.cache import cache_get, cache_set, cache_delete_pattern

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
    cache_delete_pattern("centres:*")
    return centre

@router.get("/centres", response_model=Page[CentreResponse])
def list_centres(
    page:int = Query(1, ge=1),
    page_size:int=Query(10,ge=1,le=50),
    db: Session = Depends(get_db),
):
    cache_key=f"centres:page={page}:size={page_size}"
    cached=cache_get(cache_key)
    if cached is not None:
        return Page[CentreResponse].model_validate_json(cached)

    total = db.scalar(select(func.count()).select_from(Centre))
    rows = db.scalars(
        select(Centre)
        .order_by(Centre.id)
        .offset((page-1)*page_size)
        .limit(page_size)
    ).all()
    items=[CentreResponse.model_validate(row) for row in rows]
    page_data=Page[CentreResponse](items=items, total=total,page=page,page_size=page_size)
    cache_set(cache_key, page_data.model_dump_json())
    return page_data

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

@router.get("/centres/{centre_id}/tests", response_model=Page[TestResponse])
def list_tests(
    centre_id: int,
    page:int = Query(1, ge=1),
    page_size:int=Query(10,ge=1,le=50),
    db: Session = Depends(get_db),
):
    centre=db.get(Centre,centre_id)
    if centre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centre not found")
    test_filter=DiagnosticTest.centre_id==centre.id
    total=db.scalar(select(func.count()).select_from(DiagnosticTest).where(test_filter))
    rows=db.scalars(
        select(DiagnosticTest)
        .where(test_filter)
        .order_by(DiagnosticTest.id)
        .offset((page-1)*page_size)
        .limit(page_size)
    ).all()
    return Page(items=rows, total=total,page=page,page_size=page_size)