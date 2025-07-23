from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from backend.app.auth.security import create_access_token, verify_password, SECRET_KEY, ALGORITHM
from app.db.session import get_db
from app.db.models import User
from pydantic import BaseModel, EmailStr
from backend.app.auth.security import get_password_hash

router = APIRouter(prefix="/auth", tags=["authentication"])

# 从请求头中提取令牌
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Token 响应模型
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# 用户创建模型
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# 用户响应模型
class RegisterResponse(BaseModel):
    is_registered: bool
    user: dict

# 验证用户
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# 依赖获取当前用户
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# 依赖获取当前活跃用户
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/register", response_model=RegisterResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """注册新用户"""
    # 检查用户是否已存在
    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建新用户
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "is_registered": True,
        "user": {
            "email": user.email
        }
    }

@router.post("/login", response_model=LoginResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """生成 JWT 令牌"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user.email
        }
        }