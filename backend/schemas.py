from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TokenData(BaseModel):
    id: int


class UserRead(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderRead(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class FolderRename(BaseModel):
    name: str


class AccessCreate(BaseModel):
    access_type: str
    time_unit: Optional[str] = None
    time_value: Optional[int] = None


class FileAccess(BaseModel):
    share_token: str
    expiry_time: Optional[datetime] = None

    class Config:
        from_attributes = True
