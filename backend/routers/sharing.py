from fastapi import APIRouter, status, HTTPException
from fastapi.responses import FileResponse
import os
import secrets
from database import SessionDep
from auth import CurrentUserDep
from sqlmodel import select
from models import UserFile, FilePermission
from datetime import datetime, timezone, timedelta
from schemas import FileAccess, AccessCreate


router = APIRouter()

@router.patch("{file_id}/access", response_model=FileAccess)
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


@router.get("/{token}")
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