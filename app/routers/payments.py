import uuid 

from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Booking,BookingStatus, Payment,PaymentStatus, User
from app.routers.auth import get_current_user
from app.schemas import PaymentCreate, PaymentResponse, WebhookPayload

router = APIRouter(prefix="/payments", tags=["payments"])

def to_payment_response(payment:Payment)->PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        booking_id=payment.booking_id,
        amount=payment.amount,
        status=payment.status.value,
        provider_event_id=payment.provider_event_id,
        booking_status=payment.booking.status.value,
    )

def record_payment(
    db:Session,
    booking: Booking,
    outcome: str,
    event_id: str,
) -> tuple[Payment, bool]:
    existing = db.scalar(select(Payment).where(Payment.provider_event_id == event_id))
    if existing is not None:
        return existing, False

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Booking is {booking.status.value}")

    payment_status = PaymentStatus(outcome)
    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        status=payment_status,
        provider_event_id=event_id,
    ) 
    booking.status=(
        BookingStatus.CONFIRMED
        if payment_status == PaymentStatus.SUCCESS
        else BookingStatus.FAILED
    )   
    db.add(payment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(Payment).where(Payment.provider_event_id == event_id))
        return existing, False

    db.refresh(payment)
    return payment, True

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    body: PaymentCreate,
    db: Session= Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    booking = db.get(Booking, body.booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized Not Allowed to Pay for this booking")

    payment, _ = record_payment(db, booking, body.outcome, str(uuid.uuid4()))
    return to_payment_response(payment)

@router.post("/webhook", response_model=PaymentResponse)
def payment_webhook(body: WebhookPayload, db: Session= Depends(get_db)):
    booking = db.get(Booking, body.booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment,created=record_payment(db, booking, body.status, body.event_id)
    if not created:
        return to_payment_response(payment)
    return to_payment_response(payment)