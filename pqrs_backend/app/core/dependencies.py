"""
Dependencias reutilizables para FastAPI
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.core.security import verify_token


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
):
    """Obtener usuario actual desde token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Aquí irá la lógica para buscar el usuario en la BD
    # Por ahora retornamos el payload
    return {"id": user_id, **payload}


class PaginationParams:
    """Parámetros de paginación"""
    def __init__(self, skip: int = 0, limit: int = 20):
        from app.core.config import settings
        
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'skip' no puede ser negativo"
            )
        if limit <= 0 or limit > settings.MAX_PAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'limit' debe estar entre 1 y {settings.MAX_PAGE_SIZE}"
            )
        
        self.skip = skip
        self.limit = limit


def get_pagination_params(skip: int = 0, limit: int = 20) -> PaginationParams:
    """Obtener parámetros de paginación validados"""
    return PaginationParams(skip=skip, limit=limit)
