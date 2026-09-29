from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    