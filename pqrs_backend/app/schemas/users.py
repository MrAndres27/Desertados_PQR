"""
Schemas de Usuarios
Sistema PQRS - Equipo Desertados
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict

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
    role_id: Optional[int] = None
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


# =============================================================================
# SCHEMAS DE PAGINACIÓN
# =============================================================================

class UserPaginatedResponse(BaseModel):
    """Response paginada de usuarios"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "page_size": 20,
                "total_pages": 3
            }
        }


# =============================================================================
# SCHEMAS DE ESTADÍSTICAS
# =============================================================================

class UserStatistics(BaseModel):
    """Schema de estadísticas de usuarios"""
    total: int
    active: int
    inactive: int
    by_role: Dict[str, int]
    created_last_month: int
    active_last_week: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 50,
                "active": 45,
                "inactive": 5,
                "by_role": {
                    "Administrador": 2,
                    "Gestor": 5,
                    "Supervisor": 10,
                    "Usuario": 33
                },
                "created_last_month": 8,
                "active_last_week": 35
            }
        }


# =============================================================================
# SCHEMAS DE ACCIONES
# =============================================================================

class ResetPasswordRequest(BaseModel):
    """Request para resetear contraseña (admin)"""
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_password": "NewSecure123!"
            }
        }