from fastapi import APIRouter, status, HTTPException
from schemas import FolderCreate, FolderRead, FolderRename
from database import SessionDep
from auth import CurrentUserDep
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select
from models import Folder
from typing import List
from database_operations import DatabaseOperations

router = APIRouter()

@router.post("/")
def create_folder(folder_data: FolderCreate, session: SessionDep, current_user: CurrentUserDep):
    """
    Endpoint to create a folder
    """
    if folder_data.parent_id:
        parent = session.exec(select(Folder).where(Folder.id == folder_data.parent_id)).first()

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder doesnot exist"
            )
    db_ops = DatabaseOperations(session)
    return db_ops.create_folder(folder_data.name, current_user.id, folder_data.parent_id)


@router.get("/", response_model=List[FolderRead])
def get_folder(session: SessionDep, current_user: CurrentUserDep):
    return current_user.folders


@router.patch("/{folder_id}", response_model=FolderRead)
def update_folder(folder_id: int, folder_data: FolderRename, session: SessionDep, current_user: CurrentUserDep):
    """
    Endpoint to rename the folder
    """
    folder = session.get(Folder, folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    if folder.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this folder"
        )

    db_ops = DatabaseOperations(session)
    return db_ops.update_folder(folder, folder_data.name)


@router.delete("/{folder_id}")
def delete_folder(folder_id: int, session: SessionDep, current_user: CurrentUserDep):
    """
    Endpoint to delete the folder
    """
    folder = session.get(Folder, folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    if folder.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this folder"
        )

    db_ops = DatabaseOperations(session)
    db_ops.delete_folder(folder)
    return {"message": "Folder deleted successfully"}

