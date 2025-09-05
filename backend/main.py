from fastapi import FastAPI, APIRouter

from database import init_db
from dotenv import load_dotenv

from routers import auth, folders, files, sharing, dashboard

app = FastAPI()

load_dotenv()

# Create tables in the database
init_db()


app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(folders.router, prefix="/folders", tags=["Folders"])
app.include_router(files.router, prefix="/files", tags=["Files"])
app.include_router(sharing.router, prefix="/share", tags=["File Sharing"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])


router = APIRouter()



