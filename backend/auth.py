import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from typing import Annotated
from datetime import timedelta, timezone, datetime
from database import SessionDep
from schemas import TokenData
from models import User
from sqlmodel import select


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def get_user_from_db(session, id):
    statement = select(User).where(User.id == id)
    user = session.exec(statement).first()
    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get('sub')
        if not id:
            raise credentials_exception
        token_data = TokenData(id=int(id))
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Token expired"
        )
    except InvalidTokenError:
        raise credentials_exception
    
    user = get_user_from_db(session, token_data.id)
    if not user:
        raise credentials_exception
    return user