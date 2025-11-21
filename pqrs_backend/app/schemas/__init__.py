"""Módulo de schemas Pydantic"""

from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLogin
from app.schemas.auth import Token, TokenData
from app.schemas.pqrs import PQRSCreate, PQRSUpdate, PQRSResponse

__all__ = [
    "ResponseModel",
    "PaginatedResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    "PQRSCreate",
    "PQRSUpdate",
    "PQRSResponse",
]
