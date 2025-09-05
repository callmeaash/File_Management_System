from fastapi import APIRouter
from database import SessionDep
from auth import CurrentUserDep
from models import UserFile
from sqlmodel import select
from sqlalchemy import func
router = APIRouter()


@router.get("/dashboard")
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