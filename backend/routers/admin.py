from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database.database import get_db, User, AuditLog, ComplianceRule
from routers.auth import get_current_user, require_role, get_password_hash
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["Admin"])

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str
    role: str

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

@router.get("/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db), current_user: User = Depends(require_role(["ADMIN"]))):
    return db.query(User).all()

@router.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(["ADMIN"]))):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        email=user.email,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Audit log
    db.add(AuditLog(
        username=current_user.username,
        action="CREATE_USER",
        resource_type="user",
        resource_id=new_user.username,
        detail=f"Created user {new_user.username} with role {new_user.role}"
    ))
    db.commit()
    return new_user

@router.get("/audit_logs")
def get_audit_logs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(require_role(["ADMIN"]))):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/rules")
def get_rules(db: Session = Depends(get_db), current_user: User = Depends(require_role(["ADMIN"]))):
    return db.query(ComplianceRule).all()

# Additional endpoints for rules CRUD can be added here
