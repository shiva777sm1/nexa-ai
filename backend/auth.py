from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "nexa-ai-secret-key-change-this-later"  # production mein isse .env file mein rakhna chahiye
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # token 24 hours tak valid rahega


def hash_password(password: str) -> str:
    """Plain password ko hash mein convert karta hai (save karne se pehle)"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Login ke waqt check karta hai - typed password aur saved hash match karte hain ya nahi"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """User ke liye ek JWT token banata hai (login successful hone ke baad)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Token ko verify karta hai aur uske andar ka data nikalta hai"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None