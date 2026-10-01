from datetime import datetime,timezone

from fastapi import APIRouter,Depends,HTTPException,status,Query
from sqlalchemy import select,func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, BookingStatus, DiagnosticTest, User
from app.routers.auth import get_current_user
from app.schemas import BookingCreate, BookingResponse, Page

router = APIRouter(prefix="/bookings", tags=["bookings"])

def to_booking_response(booking:Booking)->BookingResponse:
    return BookingResponse(
        id=booking.id,
        user_id=booking.user_id,
        test_id=booking.test_id,
        centre_id=booking.test.centre_id,
        test_name=booking.test.name,
        centre_name=booking.test.centre.name,
        appointment_at=booking.appointment_at,
        amount=booking.amount,
        status=booking.status.value,
    )

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    body: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.appointment_at.tzinfo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment time must be in UTC timezone")
    if body.appointment_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment time must be in the future")

    test = db.get(DiagnosticTest, body.test_id)
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    booking = Booking(
        user_id=current_user.id,
        test_id=test.id,
        appointment_at=body.appointment_at,
        amount=test.price,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return to_booking_response(booking)

@router.get("", response_model=Page[BookingResponse])
def list_bookings(
    page:int=Query(1,ge=1),
    page_size:int=Query(10,ge=1,le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking_filter=Booking.user_id == current_user.id
    total=db.scalar(select(func.count()).select_from(Booking).where(booking_filter))
    bookings=db.scalars(
        select(Booking)
        .where(booking_filter)
        .order_by(Booking.id)
        .offset((page-1)*page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[to_booking_response(booking) for booking in bookings],
        total=total,
        page=page,
        page_size=page_size,
    )

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to access this booking")
    return to_booking_response(booking)

@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to cancel this booking")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be cancelled")

    booking.status = BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return to_booking_response(booking)