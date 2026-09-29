import os
from datetime import datetime,timedelta,timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

password_hash=PasswordHash.recommended()
SECRET_KEY=os.environ["JWT_SECRET_KEY"]
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password:str, hashed_password:str) -> bool:
    return password_hash.verify(plain_password,hashed_password)

def create_access_token(user_id:int) -> str:
    expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload={"sub": str(user_id), "exp":expire}
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
