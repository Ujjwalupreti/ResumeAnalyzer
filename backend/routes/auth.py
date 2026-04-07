import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

from database import get_db
from models import User
from config import settings

router = APIRouter()
logger = logging.getLogger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# --- Simplified Request Models ---
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    current_role: str | None = None
    target_role: str | None = None
    location: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def create_access_token(user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        uid = payload.get("sub")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = User.get_by_id(int(uid))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/signup")
def signup(payload: SignupRequest):
    # 1. Check if user exists
    if User.get_by_email(payload.email):
        raise HTTPException(status_code=409, detail="User already exists")

    try:
        # 2. Create User Directly
        password_hash = pwd_context.hash(payload.password)
        user_id = User.create(
            email=payload.email,
            password_hash=password_hash,
            name=payload.name,
            current_role=payload.current_role,
            target_role=payload.target_role,
            location=payload.location
        )
        
        # 3. Return Token immediately (No OTP)
        token = create_access_token(user_id)
        logger.info(f"[signup] Created user_id={user_id} successfully.")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "message": "Signup successful."
        }
    except Exception as e:
        logger.exception(f"[signup] Unexpected error for {payload.email}: {e}")
        raise HTTPException(status_code=500, detail="Signup failed. Please try again later.")


@router.post("/login")
def login(payload: LoginRequest):
    user = User.get_by_email(payload.email)
    
    if not user or not pwd_context.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Direct login - return token immediately
    token = create_access_token(user["user_id"])
    return {
        "access_token": token, 
        "token_type": "bearer",
        "message": "Login successful."
    }


@router.get("/verify")
def verify(current_user = Depends(get_current_user)):
    return {
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "current_role": current_user.get("current_role"),
        "target_role": current_user.get("target_role"),
        "location": current_user.get("location")
    }
    
@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully"}