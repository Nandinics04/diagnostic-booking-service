import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey,Numeric,String,func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class BookingStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")

class Centre(Base):
    __tablename__ = "centres"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    tests: Mapped[list["DiagnosticTest"]] = relationship(back_populates="centre")

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"
    id: Mapped[int] = mapped_column(primary_key=True)
    centre_id: Mapped[int] = mapped_column(ForeignKey("centres.id"))
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    centre: Mapped["Centre"] = relationship(back_populates="tests")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="test")

class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    test_id: Mapped[int] = mapped_column(ForeignKey("diagnostic_tests.id"))
    appointment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="bookings")
    test: Mapped["DiagnosticTest"] = relationship(back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")
    
class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status")
    )
    provider_event_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    booking: Mapped["Booking"] = relationship(back_populates="payments")
