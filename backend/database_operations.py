from models import User, UserFile, Folder, FilePermission
from typing import Optional
from sqlmodel import Session
from exceptions import handle_db_errors
from utils import verify_password


class DatabaseOperations:
    """Centralized database operations with built-in error handling"""
    
    def __init__(self, session: Session):
        self.session = session
    
    @handle_db_errors("user creation")
    def create_user(self, email: str, hashed_password: str) -> User:
        new_user = User(email=email, password=hashed_password)
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user
    
    @handle_db_errors("folder creation")
    def create_folder(self, name: str, owner_id: int, parent_id: Optional[int] = None) -> Folder:
        new_folder = Folder(name=name, owner_id=owner_id, parent_id=parent_id)
        self.session.add(new_folder)
        self.session.commit()
        self.session.refresh(new_folder)
        return new_folder
    
    @handle_db_errors("folder update")
    def update_folder(self, folder: Folder, name: str) -> Folder:
        folder.name = name
        self.session.add(folder)
        self.session.commit()
        self.session.refresh(folder)
        return folder
    
    @handle_db_errors("folder deletion")
    def delete_folder(self, folder: Folder) -> None:
        self.session.delete(folder)
        self.session.commit()
    
    @handle_db_errors("file creation")
    def create_file(self, file_data: dict) -> UserFile:
        new_file = UserFile(**file_data)
        self.session.add(new_file)
        self.session.commit()
        self.session.refresh(new_file)
        
        # Create file permission
        new_permission = FilePermission(file_id=new_file.id)
        self.session.add(new_permission)
        self.session.commit()
        return new_file
    
    @handle_db_errors("file deletion")
    def delete_file(self, file: UserFile) -> None:
        self.session.delete(file)
        self.session.commit()
    
    @handle_db_errors("permission update")
    def update_file_permission(self, permission: FilePermission) -> FilePermission:
        self.session.add(permission)
        self.session.commit()
        self.session.refresh(permission)
        return permission
    
    @handle_db_errors("user authentication")
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with comprehensive error handling"""
        user = self.get_user_by_email(email)
        
        if not user:
            return None
            
        if not verify_password(password, user.password):
            return None
            
        return user