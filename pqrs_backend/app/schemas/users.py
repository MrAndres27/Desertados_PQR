"""
Schemas de Usuarios
Sistema PQRS - Equipo Desertados
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """Base para usuarios"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=3, max_length=200)
    document_type: str = Field(..., description="Tipo de documento: CC, CE, TI, etc.")
    document_number: str = Field(..., min_length=5, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=200)

class UserCreate(UserBase):
    """Schema para crear usuario"""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Schema de respuesta de usuario (sin contraseña)"""
    id: int
    role_id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True