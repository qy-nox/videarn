from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
def hash_password(value: str) -> str: return pwd_context.hash(value)
def verify_password(value: str, hashed: str) -> bool: return pwd_context.verify(value, hashed)
def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": subject, "type": token_type, "iat": now, "exp": now + expires_delta}, get_settings().secret_key, algorithm=ALGORITHM)
def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
