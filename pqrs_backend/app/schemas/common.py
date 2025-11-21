"""Schemas comunes reutilizables"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel):
    """Modelo de respuesta estándar"""
    success: bool
    message: str
    data: Optional[dict] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

