from fastapi import APIRouter, status, HTTPException
from schemas import FolderCreate, FolderRead, FolderRename
from database import SessionDep
from auth import CurrentUserDep
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select
from models import Folder
from typing import List


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
    try:
        new_folder = Folder(
            name=folder_data.name,
            owner_id=current_user.id,
            parent_id=folder_data.parent_id
        )
        session.add(new_folder)
        session.commit()
        session.refresh(new_folder)
    except IntegrityError:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder with that name already exists"
            )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create folder"
        )
    return new_folder


@router.get("/", response_model=List[FolderRead])
def get_folder(session: SessionDep, current_user: CurrentUserDep):
    folders = session.exec(select(Folder)).all()
    return folders


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

    try:
        folder.name = folder_data.name
        session.add(folder)
        session.commit()
        session.refresh(folder)
    except IntegrityError:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder with that name already exists"
            )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create folder"
        )
    return folder


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

    try:
        session.delete(folder)
        session.commit()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create folder"
        )

    return {"message": "Folder deleted successfully"}

