from fastapi import APIRouter, status, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import os
import shutil
from database import SessionDep
from auth import CurrentUserDep
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from models import Folder, UserFile, FilePermission
from typing import List, Optional
from datetime import datetime, timezone


router = APIRouter()


@router.post("/", status_code=status.HTTP_200_OK)
def upload_file(session: SessionDep, current_user: CurrentUserDep, file: UploadFile = File(...), folder_id: Optional[int] = None):
    """
    Endpoint for user to upload files
    """
lets md
    # Ensure the folder with the id exists and belongs to the user
    if folder_id:
        folder = session.get(Folder, folder_id)
        if not folder or folder.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder not found or not yours"
            )
    else:
        folder = None

    # Create a separate dir for each user using their id for uniqueness
    user_dir = os.path.join("uploads", str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    filename = file.filename.replace(" ", "_").strip()
    file_path = os.path.join(user_dir, filename)

    # Incase the filename already exists
    if os.path.exists(file_path):
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now(timezone.utc).timestamp())}{ext}"
        file_path = os.path.join(user_dir, filename)

    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    try:
        new_file = UserFile(
            owner_id=current_user.id,
            filename=file.filename.replace(' ', '_'),
            filepath=file_path,
            filesize=file_size,
            upload_date=datetime.now(timezone.utc),
            mime_type=file.content_type,
            folder_id=folder.id if folder else None
        )

        session.add(new_file)
        session.commit()
        session.refresh(new_file)

        new_permission = FilePermission(file_id=new_file.id)
        session.add(new_permission)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {e}"
        )
    return {"message": "File uploaded successfully"}


@router.get("/", response_model=List[UserFile])
def get_files(session: SessionDep, current_user: CurrentUserDep):
    """
    Endpoint to return all the files upload by a user
    """
    files = current_user.files
    return files


@router.get("/{folder_id}/files", response_model=List[UserFile])
def get_files_from_a_folder(folder_id: int, session: SessionDep, current_user: CurrentUserDep):
    """
    Endpoint to return all the files in a folder
    """
    folder = session.get(Folder, folder_id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    files = folder.files
    return files


@router.get("/{file_id}",)
def download_file_by_id(file_id: int, session: SessionDep, current_user: CurrentUserDep):
    """
    Endpoint to Download file by id
    """
    file = session.exec(
        select(UserFile)
        .where((UserFile.id == file_id) & (UserFile.owner_id == current_user.id))
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    file.download_count += 1
    session.add(file)
    session.commit()
    return FileResponse(
        path=file.filepath,
        filename=file.filename,
        media_type=file.mime_type
    )


@router.delete("{file_id}", status_code=status.HTTP_200_OK)
def delete_file(file_id: int, session: SessionDep, current_user: CurrentUserDep):
    file = session.exec(
        select(UserFile)
        .where((UserFile.id == file_id) & (UserFile.owner_id == current_user.id))
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    filepath = file.filepath
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    try:
        session.delete(file)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete the file"
        )
    return {"message": "File deleted Successfully"}

