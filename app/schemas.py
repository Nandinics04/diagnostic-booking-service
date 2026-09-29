from pydantic import BaseModel, ConfigDict, EmailStr, Field
from decimal import Decimal
from datetime import datetime

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

    

