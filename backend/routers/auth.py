from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserRead, Token
from typing import Annotated
from datetime import timedelta
from database import SessionDep
from auth import create_access_token
from database_operations import DatabaseOperations
from sqlmodel import select
from utils import get_password_hash, verify_password
from models import User
import os


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(form_data: UserRead, session: SessionDep):
    """
    Endpoint for new user registeration
    """
    hashed_password = get_password_hash(form_data.password)
    db_ops = DatabaseOperations(session)
    db_ops.create_user(form_data.email, hashed_password)
    return {"message": "User registered Successfuly"}


@router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    """
    Login endpoint for user to log in into the system
    """
    email = form_data.username
    password = form_data.password
    
    db_ops = DatabaseOperations(session)
    user = db_ops.authenticate_user(email, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    access_token_expires = timedelta(minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')))
    access_token = create_access_token(
        data={'sub': str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type='bearer')
