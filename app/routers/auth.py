import jwt
from fastapi import APIRouter, Depends,HTTPException,status,Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.limiter import limiter
from app.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)


router=APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token:str = Depends(oauth2_scheme),
    db:Session =Depends(get_db),
) -> User:
    credentials_error=HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload= jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id= payload.get('sub')
        if user_id is None:
            raise credentials_error
    except jwt.InvalidTokenError:
        raise credentials_error
        
    user=db.get(User, int(user_id))
    if user is None:
        raise credentials_error
    return user

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, db:Session= Depends(get_db)):
    user=User(
        full_name=body.full_name,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User with this email already exists")
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db:Session = Depends(get_db),
):
    user=db.scalar(select(User).where(User.email==form.username))
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "access_token": create_access_token(user.id),
        "token_type": "Bearer",
    }

@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


