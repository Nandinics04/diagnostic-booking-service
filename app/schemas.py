from pydantic import BaseModel, ConfigDict, EmailStr, Field
from decimal import Decimal
from datetime import datetime
from typing import Literal
from typing import Generic, TypeVar

T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    items:list[T]
    total:int
    page:int
    page_size:int

class UserCreate(BaseModel):
    full_name: str =Field(min_length=3, max_length=25)
    email: EmailStr
    password: str = Field(min_length=7, max_length=25)

class UserResponse(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id: int
    full_name:str
    email:EmailStr

class Token(BaseModel):
    access_token:str
    token_type:str = "Bearer"

class CentreCreate(BaseModel):
    name:str =Field(min_length=3, max_length=255)
    location: str=Field(min_length=3, max_length=255)

class CentreResponse(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id:int
    name:str
    location:str

class TestCreate(BaseModel):
    name:str =Field(min_length=3, max_length=25)
    price: Decimal =Field(gt=0, max_digits=10, decimal_places=2)

class TestResponse(BaseModel):
    model_config= ConfigDict(from_attributes=True)

    id:int
    name:str
    price:Decimal

class BookingCreate(BaseModel):
    test_id:int
    appointment_at:datetime

class BookingResponse(BaseModel):
    id:int
    user_id:int
    test_id:int
    centre_id:int
    test_name:str
    centre_name:str
    appointment_at:datetime
    amount:Decimal
    status:str

class PaymentCreate(BaseModel):
    booking_id:int
    outcome:Literal["SUCCESS", "FAILED"]

class WebhookPayload(BaseModel):
    event_id: str = Field(min_length=3, max_length=255)
    booking_id: int
    status:Literal["SUCCESS", "FAILED"]

class PaymentResponse(BaseModel):
    id:int
    booking_id:int
    amount:Decimal
    status: str
    provider_event_id:str | None
    booking_status: str

    

