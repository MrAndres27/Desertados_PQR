"""Schemas de Autenticación"""
from pydantic import BaseModel

class Token(BaseModel):
    """Token de acceso"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Datos del token"""
    user_id: int
    username: str
    role: str
