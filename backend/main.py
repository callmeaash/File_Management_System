from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse
from datetime import datetime, timezone, timedelta
from auth import create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from typing import Annotated, List, Optional
from database import init_db, SessionDep
from models import User, UserFile, Folder, FilePermission
from schemas import UserRead, Token, FolderCreate, FolderRead, FolderRename, AccessCreate, FileAccess
from sqlalchemy import func
from utils import get_password_hash, verify_password
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from dotenv import load_dotenv
import os
import shutil
import secrets


app = FastAPI()

load_dotenv()

# Create tables in the database
init_db()

# Dependecy for currently logged in user
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(form_data: UserRead, session: SessionDep):
    """
    Endpoint for new user registeration
    """
    hashed_password = get_password_hash(form_data.password)
    try:
        new_user = User(
            email=form_data.email,
            password=hashed_password
        )
        session.add(new_user)
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists with that email"
        )

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )
    return {"message": "User registered Successfuly"}


@app.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    """
    Login endpoint for user to log in into the system
    """
    email = form_data.username
    password = form_data.password
    
    query = select(User).where(User.email == email)
    user = session.exec(query).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password"
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password"
        )
    access_token_expires = timedelta(minutes=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')))
    access_token = create_access_token(
        data={'sub': str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type='bearer')


@app.post("/folders")
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

@app.get("/me")
def read_current_user(current_user: CurrentUserDep):
    return {
        "id": current_user.id,
        "email": current_user.email
    }

@app.get("/folders", response_model=List[FolderRead])
def get_folder(session: SessionDep, current_user: CurrentUserDep):
    folders = session.exec(select(Folder)).all()
    return folders


@app.patch("/folders/{folder_id}", response_model=FolderRead)
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


@app.delete("/folders/{folder_id}")
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


@app.post("/files", status_code=status.HTTP_200_OK)
def upload_file(session: SessionDep, current_user: CurrentUserDep, file: UploadFile = File(...), folder_id: Optional[int] = None):
    """
    Endpoint for user to upload files
    """

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


@app.get("/files", response_model=List[UserFile])
def get_files(session: SessionDep, current_user: CurrentUserDep):
    """
    Endpoint to return all the files upload by a user
    """
    files = current_user.files
    return files


@app.get("/folders/{folder_id}/files", response_model=List[UserFile])
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


@app.get("/files/{file_id}",)
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


@app.delete("/files/{file_id}", status_code=status.HTTP_200_OK)
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


@app.patch("/files/{file_id}/access", response_model=FileAccess)
def change_access_type(file_id, access_data: AccessCreate, session: SessionDep, current_user: CurrentUserDep):

    file = session.exec(select(UserFile).where(UserFile.id == file_id)).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if file.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You donot have the right to modify this file"
        )

    if access_data.access_type not in ['only_me', 'anyone_with_link', 'timed_access']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid access type"
        )

    file_permission = session.exec(
        select(FilePermission)
        .where(FilePermission.file_id == file.id)
    ).first()
    share_token = secrets.token_urlsafe(32)
    if access_data.access_type == 'anyone_with_link':
        file_permission.access_type = access_data.access_type
        file_permission.share_token = share_token

        session.add(file_permission)
        session.commit()

    elif access_data.access_type == 'timed_access':
        if access_data.time_unit not in ['days', 'minutes', 'hours']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time unit, must be ['days', 'minutes', 'hours']"
            )
        if access_data.time_value <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time value must be positive"
            )
        kwargs = {access_data.time_unit: access_data.time_value}
        expiry_time = datetime.now(timezone.utc) + timedelta(**kwargs)
        file_permission.access_type = access_data.access_type
        file_permission.share_token = share_token
        file_permission.expiry_time = expiry_time
        session.add(file_permission)
        session.commit()
        session.refresh(file_permission)

    return file_permission


@app.get("/share/{token}")
def get_file_by_token(token: str, session: SessionDep):
    """
    Endpoint to return file through access link
    """
    file_permission = session.exec(
        select(FilePermission)
        .where(FilePermission.share_token == token)
    ).first()

    if not file_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid link"
        )
    
    file = session.exec(
            select(UserFile)
            .where(UserFile.id == file_permission.file_id)
        ).first()
    
    if not os.path.exists(file.filepath):
        raise HTTPException(status_code=404, detail="File missing on server")
    
    file_response = FileResponse(
        path=file.filepath,
        filename=file.filename,
        media_type=file.mime_type
    )
    file.download_count += 1
    session.add(file)
    session.commit()
    if file_permission.access_type == 'anyone_with_link':
        return file_response
    
    elif file_permission.access_type == 'timed_access':
        if file_permission.expiry_time < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link already expired"
            )
        return file_response

@app.get("/dashboard")
def dashboard(session: SessionDep, current_user: CurrentUserDep):
    files = current_user.files
    files_count = len(files)

    total_storage = session.exec(
        select(func.sum(UserFile.filesize))
        .where(UserFile.owner_id == current_user.id)
    ).one()

    total_storage = total_storage or 0

    total_downloads = session.exec(
        select(func.sum(UserFile.download_count))
        .where(UserFile.owner_id == current_user.id)
    ).one()

    return {
        "total_files": files_count,
        "total_storage": total_storage,
        "total_downloads": total_downloads
    }



