from passlib.context import CryptContext


pwd_context = CryptContext(schemes=['bcrypt'])


def get_password_hash(plain_password) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)