from pydantic import BaseModel, ConfigDict, EmailStr, Field
from decimal import Decimal

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

