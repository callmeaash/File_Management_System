from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os
from typing import Annotated
from fastapi import Depends

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def init_db():
    SQLModel.metadata.create_all(engine)