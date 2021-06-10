
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET")
ALGORITHM = "HS256"
AUDIENCE = "fastapi-users:auth"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=os.getenv("AUTH_ENDPOINT"))


class TokenData(BaseModel):
    user_id: str = ...


async def validate_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=AUDIENCE)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    return token_data
