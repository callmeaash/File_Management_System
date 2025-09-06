from fastapi import HTTPException, status
import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from functools import wraps
from typing import Callable, Any


logger = logging.getLogger()


class DatabaseError(HTTPException):
    """Custom database error with specific error messages"""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


def handle_database_error(e: SQLAlchemyError, operation: str) -> None:
    """
    Extract specific error and raise appropriate exception
    """
    logger.error(f"Database error during {operation}: {str(e)}")
    
    if isinstance(e, IntegrityError):
        error_msg = str(e.orig).lower() if e.orig else str(e).lower()
        
        if 'unique constraint' in error_msg or 'duplicate' in error_msg:
            if 'email' in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
        
        elif 'foreign key constraint' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referenced resource does not exist"
            )
        
        elif 'not null constraint' in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Required field is missing"
            )
        
        else:
            # Generic integrity error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity violation during {operation}"
            )
    
    # Handle other specific SQLAlchemy errors
    elif 'connection' in str(e).lower():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error. Please try again later."
        )
    
    elif 'timeout' in str(e).lower():
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Database operation timed out. Please try again."
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error occurred during {operation}"
        )


def handle_db_errors(operation_name: str):
    """Decorator to handle database errors for any function"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except (IntegrityError, SQLAlchemyError) as e:
                handle_database_error(e, operation_name)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Unexpected error during {operation_name}"
                )
        return wrapper
    return decorator