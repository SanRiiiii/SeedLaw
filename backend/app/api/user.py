from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.db.models import User, CompanyInfo
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])

# Company info model
class CompanyInfoModel(BaseModel):
    company_name: str
    industry: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    company_size: Optional[str] = None
    business_scope: Optional[str] = None
    additional_info: Optional[dict] = None
    
    class Config:
        orm_mode = True

# User with company info
class UserWithCompany(BaseModel):
    id: int
    email: str
    company_info: Optional[CompanyInfoModel] = None
    
    class Config:
        orm_mode = True

@router.get("/me", response_model=UserWithCompany)
def read_user_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information including company details"""
    return current_user

@router.put("/company-info", response_model=CompanyInfoModel)
def update_company_info(
    company_data: CompanyInfoModel,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update or create company information for current user"""
    # Check if company info exists
    if current_user.company_info:
        # Update existing
        for key, value in company_data.dict(exclude_unset=True).items():
            setattr(current_user.company_info, key, value)
    else:
        # Create new
        company_info = CompanyInfo(**company_data.dict(), user_id=current_user.id)
        db.add(company_info)
    
    db.commit()
    db.refresh(current_user)
    return current_user.company_info