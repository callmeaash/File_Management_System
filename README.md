# File Sharing Application Backend

A FastAPI-based file sharing service that allows users to upload, manage, organize, and securely share files with flexible access controls.

## Features

- **User Authentication**: Secure user registration and login with JWT token-based authentication
- **File Management**: Upload, download, and delete files with automatic duplicate handling
- **Folder Organization**: Create, rename, and delete folders with hierarchical structure support
- **File Sharing**: Share files with multiple access control options:
  - Private (only me)
  - Public link sharing (anyone with link)
  - Time-limited access (automatic expiration)
- **Dashboard Analytics**: Track total files, storage usage, and download counts
- **Error Handling**: Comprehensive database error handling with specific error messages
- **Per-User Storage**: Isolated storage directories for each user

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLModel with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with OAuth2
- **Password Hashing**: Bcrypt via Passlib
- **Environment**: Python-dotenv

## Project Structure

```
backend/
├── main.py                    # FastAPI app initialization and router setup
├── auth.py                    # JWT authentication logic and dependencies
├── database.py                # Database connection and session management
├── models.py                  # SQLModel database models
├── schemas.py                 # Pydantic request/response models
├── utils.py                   # Utility functions (password hashing)
├── exceptions.py              # Custom error handling and decorators
├── database_operations.py      # Centralized database operations
├── routers/
│   ├── auth.py               # User registration and login endpoints
│   ├── files.py              # File upload, download, and deletion endpoints
│   ├── folders.py            # Folder management endpoints
│   ├── sharing.py            # File sharing and access control endpoints
│   └── dashboard.py          # User dashboard analytics endpoints
└── uploads/                   # User file storage (auto-created)
```

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token

### Files (`/files`)
- `POST /files/` - Upload a file (supports optional folder_id)
- `GET /files/` - Get all user files
- `GET /files/{folder_id}/files` - Get files in a specific folder
- `GET /files/{file_id}` - Download file by ID
- `DELETE /files/{file_id}` - Delete a file

### Folders (`/folders`)
- `POST /folders/` - Create a new folder
- `GET /folders/` - Get all user folders
- `PATCH /folders/{folder_id}` - Rename a folder
- `DELETE /folders/{folder_id}` - Delete a folder

### File Sharing (`/share`)
- `PATCH /share/{file_id}/access` - Change file access permissions
- `GET /share/{token}` - Download file using share token

### Dashboard (`/dashboard`)
- `GET /dashboard/dashboard` - Get user analytics (total files, storage, downloads)

## Database Models

### User
```python
- id: int (primary key)
- email: str (unique)
- password: str (hashed)
- files: List[UserFile] (relationship)
- folders: List[Folder] (relationship)
```

### UserFile
```python
- id: int (primary key)
- owner_id: int (foreign key)
- folder_id: Optional[int] (foreign key)
- filename: str
- filepath: str
- filesize: int
- upload_date: datetime
- mime_type: str
- download_count: int
```

### Folder
```python
- id: int (primary key)
- owner_id: int (foreign key)
- name: str
- created_at: datetime
- parent_id: Optional[int] (self-referencing foreign key for hierarchy)
- files: List[UserFile] (relationship)
```

### FilePermission
```python
- id: int (primary key)
- file_id: int (foreign key, unique)
- access_type: str (only_me, anyone_with_link, timed_access)
- share_token: Optional[str]
- expiry_time: Optional[datetime]
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- SQLite or PostgreSQL database

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd backend
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install fastapi uvicorn sqlmodel sqlalchemy python-jose[cryptography] passlib[bcrypt] python-dotenv
```

4. **Configure environment variables**

Create a `.env` file in the backend directory:
```
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

For production with PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost/dbname
```

5. **Run the application**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Usage Examples

### Register a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### Upload a File
```bash
curl -X POST "http://localhost:8000/files/" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/file.txt"
```

### Create a Folder
```bash
curl -X POST "http://localhost:8000/folders/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Folder"}'
```

### Share a File with Time Limit
```bash
curl -X PATCH "http://localhost:8000/share/1/access" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "access_type": "timed_access",
    "time_unit": "hours",
    "time_value": 24
  }'
```

### Get Dashboard Analytics
```bash
curl -X GET "http://localhost:8000/dashboard/dashboard" \
  -H "Authorization: Bearer <token>"
```

## Security Features

- **Password Hashing**: All passwords are hashed using Bcrypt
- **JWT Authentication**: Token-based authentication with expiration
- **Authorization Checks**: File and folder operations are restricted to owners
- **Unique Constraints**: Email uniqueness and folder name-parent-owner combinations
- **Secure Sharing**: Tokens are generated using cryptographically secure random strings
- **Error Handling**: Detailed error logging without exposing sensitive information

## Error Handling

The application includes comprehensive error handling for:
- Database integrity violations (duplicate emails, constraint violations)
- Foreign key violations (referencing non-existent resources)
- Authentication and authorization failures
- File not found errors
- Connection and timeout issues

All errors return appropriate HTTP status codes with descriptive messages.

## Key Design Patterns

- **Dependency Injection**: FastAPI's dependency system for session and user management
- **Custom Decorators**: `@handle_db_errors` for centralized error handling
- **Relationships**: SQLModel relationships for easy data access
- **Type Hints**: Full type annotation for better code clarity and IDE support


## Support

For issues or questions, please create an issue in the repository or contact the development team.
