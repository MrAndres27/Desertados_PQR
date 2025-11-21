"""
Dependencias reutilizables para FastAPI
Sistema PQRS - Equipo Desertados

Proporciona:
- get_current_user: Obtiene usuario autenticado desde JWT
- get_current_active_user: Verifica que el usuario esté activo
- require_role: Verifica que el usuario tenga un rol específico
- require_permission: Verifica permisos específicos
- PaginationParams: Parámetros de paginación validados
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.core.security import verify_token
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission

# Security scheme para JWT
security = HTTPBearer()


# =============================================================================
# DEPENDENCIAS DE AUTENTICACIÓN
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Obtiene el usuario actual autenticado desde el token JWT
    
    Args:
        credentials: Credenciales Bearer con el token JWT
        db: Sesión de base de datos
        
    Returns:
        User: Usuario autenticado
        
    Raises:
        HTTPException 401: Si el token es inválido o el usuario no existe
        
    Ejemplo:
        @app.get("/profile")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return {"username": current_user.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extraer token
    token = credentials.credentials
    
    # Verificar token
    payload = verify_token(token, token_type="access")
    if payload is None:
        raise credentials_exception
    
    # Extraer user_id del token
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Buscar usuario en base de datos con su rol y permisos
    result = await db.execute(
        select(User)
        .options(
            # Cargar relaciones necesarias
            selectinload(User.role).selectinload(Role.permissions)
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtiene el usuario actual y verifica que esté activo
    
    Args:
        current_user: Usuario obtenido de get_current_user
        
    Returns:
        User: Usuario activo
        
    Raises:
        HTTPException 403: Si el usuario está inactivo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


# =============================================================================
# DEPENDENCIAS DE AUTORIZACIÓN (Roles y Permisos)
# =============================================================================

class RoleChecker:
    """
    Dependency para verificar que el usuario tenga un rol específico
    
    Ejemplo:
        @app.get("/admin/users")
        async def list_users(
            current_user: User = Depends(RoleChecker(["Administrador", "Gestor"]))
        ):
            # Solo accesible por Administrador o Gestor
            ...
    """
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere uno de estos roles: {', '.join(self.allowed_roles)}"
            )
        return current_user


class PermissionChecker:
    """
    Dependency para verificar que el usuario tenga permisos específicos
    
    Ejemplo:
        @app.post("/pqrs")
        async def create_pqrs(
            current_user: User = Depends(PermissionChecker(["crear_pqrs"]))
        ):
            # Solo accesible con permiso crear_pqrs
            ...
    """
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Obtener nombres de permisos del usuario
        user_permissions = [p.name for p in current_user.role.permissions]
        
        # Verificar que tenga todos los permisos requeridos
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permiso requerido: {permission}"
                )
        
        return current_user


# Funciones helper para roles comunes
def require_admin():
    """Requiere rol de Administrador"""
    return RoleChecker(["Administrador"])


def require_admin_or_manager():
    """Requiere rol de Administrador o Gestor"""
    return RoleChecker(["Administrador", "Gestor"])


def require_staff():
    """Requiere rol de staff (Administrador, Gestor o Supervisor)"""
    return RoleChecker(["Administrador", "Gestor", "Supervisor"])


# =============================================================================
# DEPENDENCIAS DE PAGINACIÓN
# =============================================================================

class PaginationParams:
    """Parámetros de paginación con validación"""
    
    def __init__(self, skip: int = 0, limit: int = 20):
        from app.core.config import settings
        
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'skip' no puede ser negativo"
            )
        
        max_size = getattr(settings, 'MAX_PAGE_SIZE', 100)
        if limit <= 0 or limit > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'limit' debe estar entre 1 y {max_size}"
            )
        
        self.skip = skip
        self.limit = limit


def get_pagination_params(skip: int = 0, limit: int = 20) -> PaginationParams:
    """Obtiene parámetros de paginación validados"""
    return PaginationParams(skip=skip, limit=limit)


# =============================================================================
# DEPENDENCIAS PARA BÚSQUEDA Y FILTRADO
# =============================================================================

class SearchParams:
    """Parámetros de búsqueda y filtrado"""
    
    def __init__(
        self,
        q: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: str = "asc"
    ):
        self.q = q
        self.sort_by = sort_by
        self.order = order.lower()
        
        if self.order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'order' debe ser 'asc' o 'desc'"
            )


def get_search_params(
    q: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = "asc"
) -> SearchParams:
    """Obtiene parámetros de búsqueda validados"""
    return SearchParams(q=q, sort_by=sort_by, order=order)