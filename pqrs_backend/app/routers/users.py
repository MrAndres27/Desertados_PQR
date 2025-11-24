"""
Router de Usuarios
Sistema PQRS - Equipo Desertados

Endpoints de administración de usuarios (solo admin):
- GET /users - Listar usuarios
- GET /users/{id} - Ver usuario
- PUT /users/{id} - Actualizar usuario
- DELETE /users/{id} - Eliminar usuario
- PUT /users/{id}/activate - Activar usuario
- PUT /users/{id}/deactivate - Desactivar usuario
- POST /users/{id}/reset-password - Resetear password
- GET /users/statistics - Estadísticas de usuarios
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math

from app.core.database import get_async_db
from app.core.dependencies import (
    get_current_user,
    get_pagination_params,
    PaginationParams,
    require_admin
)
from app.services.user_service import UserService, get_user_service
from app.models.user import User
from app.schemas.users import (
    UserResponse,
    UserUpdate,
    UserPaginatedResponse,
    UserStatistics,
    ResetPasswordRequest
)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(
    prefix="/users",
    tags=["Usuarios (Admin)"]
)


# =============================================================================
# ENDPOINTS DE CONSULTA
# =============================================================================

@router.get("", response_model=UserPaginatedResponse, status_code=status.HTTP_200_OK)
async def list_users(
    # Paginación
    pagination: PaginationParams = Depends(get_pagination_params),
    # Filtros
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    role_id: Optional[int] = Query(None, description="Filtrar por rol"),
    search: Optional[str] = Query(None, description="Buscar en username, email o nombre"),
    # Dependencias
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista todos los usuarios con filtros opcionales y paginación
    
    **Filtros disponibles:**
    - `is_active`: true/false para usuarios activos/inactivos
    - `role_id`: ID del rol
    - `search`: Texto a buscar en username, email o full_name
    
    **Paginación:**
    - `skip`: Registros a saltar (default: 0)
    - `limit`: Límite de resultados (default: 20, max: 100)
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    user_service = get_user_service(db)
    
    users_list, total = await user_service.list_users(
        skip=pagination.skip,
        limit=pagination.limit,
        is_active=is_active,
        role_id=role_id,
        search=search
    )
    
    # Calcular paginación
    page = (pagination.skip // pagination.limit) + 1
    total_pages = math.ceil(total / pagination.limit) if total > 0 else 1
    
    return UserPaginatedResponse(
        items=users_list,
        total=total,
        page=page,
        page_size=pagination.limit,
        total_pages=total_pages
    )


@router.get("/statistics", response_model=UserStatistics, status_code=status.HTTP_200_OK)
async def get_statistics(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas generales de usuarios
    
    Incluye:
    - Total de usuarios
    - Usuarios activos/inactivos
    - Distribución por rol
    - Usuarios creados en el último mes
    - Usuarios activos en la última semana
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    user_service = get_user_service(db)
    
    stats = await user_service.get_statistics()
    
    return UserStatistics(**stats)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene el detalle completo de un usuario por ID
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    user_service = get_user_service(db)
    
    user = await user_service.get_user_by_id(user_id)
    
    return user


# =============================================================================
# ENDPOINTS DE MODIFICACIÓN
# =============================================================================

@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza información de un usuario
    
    Solo se actualizan los campos proporcionados (partial update).
    
    **Campos actualizables:**
    - email
    - full_name
    - phone
    - address
    - role_id
    - is_active
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    user_service = get_user_service(db)
    
    updated_user = await user_service.update_user(
        user_id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        address=user_data.address,
        role_id=user_data.role_id
    )
    
    # Actualizar estado si se proporcionó
    if user_data.is_active is not None:
        if user_data.is_active and not updated_user.is_active:
            updated_user = await user_service.activate_user(user_id)
        elif not user_data.is_active and updated_user.is_active:
            updated_user = await user_service.deactivate_user(user_id)
    
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina un usuario
    
    **IMPORTANTE:** Esta acción no se puede deshacer.
    
    **Nota:** No se puede eliminar el propio usuario administrador.
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    # Verificar que el admin no se está eliminando a sí mismo
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propio usuario"
        )
    
    user_service = get_user_service(db)
    
    success = await user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el usuario"
        )
    
    return {
        "message": "Usuario eliminado exitosamente",
        "user_id": user_id,
        "success": True
    }


# =============================================================================
# ENDPOINTS DE GESTIÓN DE ESTADO
# =============================================================================

@router.put("/{user_id}/activate", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Activa un usuario desactivado
    
    Permite que el usuario pueda volver a iniciar sesión.
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    user_service = get_user_service(db)
    
    user = await user_service.activate_user(user_id)
    
    return user


@router.put("/{user_id}/deactivate", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Desactiva un usuario
    
    El usuario no podrá iniciar sesión hasta que sea activado nuevamente.
    
    **Nota:** No se puede desactivar el propio usuario administrador.
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    # Verificar que el admin no se está desactivando a sí mismo
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio usuario"
        )
    
    user_service = get_user_service(db)
    
    user = await user_service.deactivate_user(user_id)
    
    return user


# =============================================================================
# ENDPOINTS DE GESTIÓN DE CONTRASEÑA
# =============================================================================

@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    user_id: int,
    request: ResetPasswordRequest,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Resetea la contraseña de un usuario (solo admin)
    
    La nueva contraseña debe cumplir con los requisitos de seguridad:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    
    **Requiere:** Usuario autenticado con rol de Administrador
    """
    user_service = get_user_service(db)
    
    success = await user_service.reset_password(
        user_id=user_id,
        new_password=request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al resetear la contraseña"
        )
    
    return {
        "message": "Contraseña reseteada exitosamente",
        "user_id": user_id,
        "success": True
    }


# =============================================================================
# NOTAS DE IMPLEMENTACIÓN
# =============================================================================

"""
SEGURIDAD IMPLEMENTADA:

1. Todos los endpoints requieren autenticación (Bearer token)
2. Todos los endpoints requieren rol de Administrador
3. El admin no puede:
   - Eliminarse a sí mismo
   - Desactivarse a sí mismo
4. Validaciones de seguridad:
   - Email único al actualizar
   - Contraseña fuerte al resetear
   - Verificación de existencia de roles

PERMISOS:
- Solo usuarios con rol "Administrador" pueden acceder
- Implementado con require_admin() dependency

ENDPOINTS PROTEGIDOS:
- GET /users → require_admin()
- GET /users/{id} → require_admin()
- PUT /users/{id} → require_admin()
- DELETE /users/{id} → require_admin()
- PUT /users/{id}/activate → require_admin()
- PUT /users/{id}/deactivate → require_admin()
- POST /users/{id}/reset-password → require_admin()
- GET /users/statistics → require_admin()

CASOS DE USO:

1. Listar usuarios:
   - Admin ve todos los usuarios
   - Puede filtrar por activos/inactivos
   - Puede filtrar por rol
   - Puede buscar por texto

2. Ver detalle:
   - Admin ve información completa del usuario
   - Incluyendo rol y permisos

3. Actualizar:
   - Admin puede cambiar datos básicos
   - Admin puede cambiar rol
   - Admin puede activar/desactivar

4. Eliminar:
   - Admin puede eliminar usuarios
   - No puede eliminarse a sí mismo

5. Gestión de estado:
   - Activar usuarios desactivados
   - Desactivar usuarios problemáticos
   - No puede desactivarse a sí mismo

6. Resetear contraseña:
   - Admin puede resetear passwords olvidados
   - Usuario debe cumplir requisitos de seguridad

7. Estadísticas:
   - Ver métricas generales
   - Distribución por roles
   - Actividad reciente
"""