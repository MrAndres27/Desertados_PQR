"""Schemas de PQRS"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PQRSBase(BaseModel):
    """Base para PQRS"""
    type: str = Field(..., pattern="^(peticion|queja|reclamo|sugerencia)$")
    subject: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    priority: str = Field(default="media", pattern="^(baja|media|alta)$")

class PQRSCreate(PQRSBase):
    """Para crear PQRS"""
    pass

class PQRSUpdate(BaseModel):
    """Para actualizar PQRS"""
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None

class PQRSResponse(PQRSBase):
    """Respuesta con PQRS"""
    id: int
    radicado_number: str
    status_id: int
    semaphore_color: str
    user_id: int
    assigned_to: Optional[int]
    due_date: datetime
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True