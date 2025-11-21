"""Schemas de Usuario"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserBase(BaseModel):
    """Base para Usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

class UserCreate(UserBase):
    """Para crear usuario"""
    password: str = Field(..., min_length=8)
    role_id: int
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class UserUpdate(BaseModel):
    """Para actualizar usuario"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Respuesta con datos de usuario"""
    id: int
    is_active: bool
    is_superuser: bool
    role_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """Para login"""
    username: str
    password: str
