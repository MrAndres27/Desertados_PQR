"""
Schemas de PQRS
Sistema PQRS - Equipo Desertados

Schemas de validación para:
- Crear PQRS
- Actualizar PQRS
- Respuestas de PQRS
- Filtros y búsquedas
"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class PQRSTypeEnum(str, Enum):
    """Tipos de PQRS"""
    PETICION = "peticion"
    QUEJA = "queja"
    RECLAMO = "reclamo"
    SUGERENCIA = "sugerencia"


class PriorityEnum(str, Enum):
    """Prioridades de PQRS"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


# =============================================================================
# SCHEMAS BASE
# =============================================================================

class PQRSBase(BaseModel):
    """Base para PQRS"""
    type: PQRSTypeEnum = Field(..., description="Tipo de PQRS")
    subject: str = Field(..., min_length=5, max_length=200, description="Asunto")
    description: str = Field(..., min_length=10, description="Descripción detallada")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIA, description="Prioridad")
    requester_name: Optional[str] = Field(None, max_length=200, description="Nombre del solicitante")
    requester_email: Optional[EmailStr] = Field(None, description="Email del solicitante")
    requester_phone: Optional[str] = Field(None, max_length=20, description="Teléfono del solicitante")


# =============================================================================
# SCHEMAS DE CREACIÓN
# =============================================================================

class PQRSCreate(PQRSBase):
    """Schema para crear PQRS"""
    assigned_to: Optional[int] = Field(None, description="ID del usuario asignado (opcional)")
    deadline_days: int = Field(default=15, ge=1, le=90, description="Días para resolver (1-90)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "peticion",
                "subject": "Solicitud de información sobre trámite",
                "description": "Requiero información detallada sobre cómo realizar el trámite de...",
                "priority": "media",
                "requester_name": "Juan Pérez",
                "requester_email": "juan@example.com",
                "requester_phone": "3001234567",
                "deadline_days": 15
            }
        }


class PQRSUpdate(BaseModel):
    """Schema para actualizar PQRS"""
    subject: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    priority: Optional[PriorityEnum] = None
    requester_name: Optional[str] = Field(None, max_length=200)
    requester_email: Optional[EmailStr] = None
    requester_phone: Optional[str] = Field(None, max_length=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Nuevo asunto actualizado",
                "priority": "alta"
            }
        }


# =============================================================================
# SCHEMAS DE RESPUESTA
# =============================================================================

class PQRSStatusResponse(BaseModel):
    """Schema de respuesta para estado de PQRS"""
    id: int
    name: str
    description: Optional[str] = None
    order: int
    is_final: bool
    color: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserBasicResponse(BaseModel):
    """Schema básico de usuario para respuestas de PQRS"""
    id: int
    username: str
    full_name: str
    email: str
    
    class Config:
        from_attributes = True


class PQRSResponse(PQRSBase):
    """Schema de respuesta completa de PQRS"""
    id: int
    radicado_number: str
    status_id: int
    status: PQRSStatusResponse
    user_id: int
    creator: UserBasicResponse
    assigned_to: Optional[int] = None
    assignee: Optional[UserBasicResponse] = None
    due_date: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "radicado_number": "PQRS-20241121-0001",
                "type": "peticion",
                "subject": "Solicitud de información",
                "description": "Descripción detallada...",
                "priority": "media",
                "status_id": 1,
                "status": {
                    "id": 1,
                    "name": "Recibida",
                    "order": 1,
                    "is_final": False
                },
                "user_id": 1,
                "creator": {
                    "id": 1,
                    "username": "juan123",
                    "full_name": "Juan Pérez",
                    "email": "juan@example.com"
                },
                "due_date": "2024-12-06T12:00:00",
                "created_at": "2024-11-21T12:00:00"
            }
        }


class PQRSListResponse(BaseModel):
    """Schema de respuesta para lista de PQRS (sin relaciones anidadas)"""
    id: int
    radicado_number: str
    type: str
    subject: str
    priority: str
    status_id: int
    user_id: int
    assigned_to: Optional[int] = None
    due_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# SCHEMAS DE ACCIONES
# =============================================================================

class ChangeStatusRequest(BaseModel):
    """Request para cambiar estado de PQRS"""
    new_status_id: int = Field(..., description="ID del nuevo estado")
    comment: Optional[str] = Field(None, max_length=500, description="Comentario sobre el cambio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_status_id": 2,
                "comment": "Se ha iniciado la revisión del caso"
            }
        }


class AssignToUserRequest(BaseModel):
    """Request para asignar PQRS a usuario"""
    user_id: int = Field(..., description="ID del usuario a asignar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 5
            }
        }


# =============================================================================
# SCHEMAS DE ESTADÍSTICAS
# =============================================================================

class PQRSStatistics(BaseModel):
    """Schema de estadísticas de PQRS"""
    total: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    by_status: Dict[str, int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "by_type": {
                    "Petición": 60,
                    "Queja": 40,
                    "Reclamo": 30,
                    "Sugerencia": 20
                },
                "by_priority": {
                    "Baja": 50,
                    "Media": 60,
                    "Alta": 30,
                    "Crítica": 10
                },
                "by_status": {
                    "Recibida": 40,
                    "En Proceso": 60,
                    "Resuelta": 45,
                    "Cerrada": 5
                }
            }
        }


# =============================================================================
# SCHEMAS DE PAGINACIÓN
# =============================================================================

class PQRSPaginatedResponse(BaseModel):
    """Response paginada de PQRS"""
    items: List[PQRSResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "page_size": 20,
                "total_pages": 8
            }
        }


# =============================================================================
# SCHEMAS DE FILTROS
# =============================================================================

class PQRSFilters(BaseModel):
    """Filtros para búsqueda de PQRS"""
    status_id: Optional[int] = None
    type: Optional[PQRSTypeEnum] = None
    priority: Optional[PriorityEnum] = None
    assigned_to: Optional[int] = None
    created_by: Optional[int] = None
    search: Optional[str] = Field(None, max_length=200, description="Búsqueda en código, asunto o descripción")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status_id": 1,
                "type": "peticion",
                "priority": "alta",
                "search": "información"
            }
        }