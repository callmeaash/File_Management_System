from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from sqlalchemy import Column, Text, ForeignKey, Enum, DateTime, func
from datetime import datetime, timezone
from typing import List, Optional


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(Text, unique=True, nullable=False))
    password: str

    files: List["UserFile"] = Relationship(back_populates="user")
    folders: List["Folder"] = Relationship(back_populates="user")


class UserFile(SQLModel, table=True):
    __tablename__ = "files"
    id: int = Field(default=None, primary_key=True)
    owner_id: int = Field(sa_column=Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False))
    folder_id: Optional[int] = Field(sa_column=Column(ForeignKey("folders.id", ondelete="SET NULL"), nullable=True))
    filesize: int
    filename: str
    filepath: str
    upload_date: datetime
    mime_type: str
    download_count: int = Field(default=0, nullable=False)

    user: User = Relationship(back_populates="files")
    folder: Optional["Folder"] = Relationship(back_populates="files")


class Folder(SQLModel, table=True):
    __tablename__ = "folders"
    __table_args__ = (
        UniqueConstraint("name", "parent_id", "owner_id", name="uq_folder_name_parent_owner"),
    )

    id: int = Field(default=None, primary_key=True)
    owner_id: int = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    name: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    parent_id: Optional[int] = Field(default=None, sa_column=Column(ForeignKey("folders.id", ondelete="CASCADE"), nullable=True))

    user: "User" = Relationship(back_populates="folders")

    files: List["UserFile"] = Relationship(back_populates="folder")


class FilePermission(SQLModel, table=True):
    __tablename__ = "file_permissions"
    id: int = Field(default=None, primary_key=True)
    file_id: int = Field(
        sa_column=Column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False, unique=True)
    )
    access_type: str = Field(
        sa_column=Column(Enum('only_me', 'anyone_with_link', 'timed_access', name='access_type_enum'), server_default='only_me', nullable=False)
    )
    share_token: Optional[str] = None
    expiry_time: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

