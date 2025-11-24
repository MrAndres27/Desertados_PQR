"""
Router de PQRS
Sistema PQRS - Equipo Desertados

Endpoints:
- POST /pqrs - Crear PQRS
- GET /pqrs - Listar PQRS (con filtros)
- GET /pqrs/{id} - Ver detalle de PQRS
- PUT /pqrs/{id} - Actualizar PQRS
- DELETE /pqrs/{id} - Eliminar PQRS
- POST /pqrs/{id}/assign - Asignar a usuario
- POST /pqrs/{id}/change-status - Cambiar estado
- GET /pqrs/my-pqrs - Mis PQRS creadas
- GET /pqrs/assigned-to-me - PQRS asignadas a mí
- GET /pqrs/overdue - PQRS vencidas
- GET /pqrs/statistics - Estadísticas
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, get_pagination_params, PaginationParams
from app.services.pqrs_service import PQRSService, get_pqrs_service
from app.models.user import User
from app.models.pqrs import PQRSType, PQRSPriority as Priority
from app.schemas.pqrs import (
    PQRSCreate,
    PQRSUpdate,
    PQRSResponse,
    PQRSPaginatedResponse,
    ChangeStatusRequest,
    AssignToUserRequest,
    PQRSStatistics
)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(
    prefix="/pqrs",
    tags=["PQRS"]
)


# =============================================================================
# ENDPOINTS DE CONSULTA
# =============================================================================

@router.get("", response_model=PQRSPaginatedResponse, status_code=status.HTTP_200_OK)
async def list_pqrs(
    # Paginación
    pagination: PaginationParams = Depends(get_pagination_params),
    # Filtros
    status_id: Optional[int] = Query(None, description="Filtrar por estado"),
    type: Optional[str] = Query(None, description="Filtrar por tipo (peticion, queja, reclamo, sugerencia)"),
    priority: Optional[str] = Query(None, description="Filtrar por prioridad (baja, media, alta, critica)"),
    assigned_to: Optional[int] = Query(None, description="Filtrar por usuario asignado"),
    created_by: Optional[int] = Query(None, description="Filtrar por creador"),
    search: Optional[str] = Query(None, description="Buscar en código, asunto o descripción"),
    # Dependencias
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Lista todas las PQRS con filtros opcionales y paginación
    
    **Filtros disponibles:**
    - `status_id`: ID del estado
    - `type`: Tipo (peticion, queja, reclamo, sugerencia)
    - `priority`: Prioridad (baja, media, alta, critica)
    - `assigned_to`: ID del usuario asignado
    - `created_by`: ID del creador
    - `search`: Texto a buscar en código, asunto o descripción
    
    **Paginación:**
    - `skip`: Registros a saltar (default: 0)
    - `limit`: Límite de resultados (default: 20, max: 100)
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    # Convertir strings a enums si es necesario
    pqrs_type_enum = None
    if type:
        try:
            pqrs_type_enum = PQRSType(type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo inválido. Valores permitidos: peticion, queja, reclamo, sugerencia"
            )
    
    priority_enum = None
    if priority:
        try:
            priority_enum = Priority(priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prioridad inválida. Valores permitidos: baja, media, alta, critica"
            )
    
    # Obtener PQRS
    pqrs_list, total = await pqrs_service.list_pqrs(
        skip=pagination.skip,
        limit=pagination.limit,
        status_id=status_id,
        pqrs_type=pqrs_type_enum,
        priority=priority_enum,
        assigned_to=assigned_to,
        created_by=created_by,
        search=search
    )
    
    # Calcular paginación
    page = (pagination.skip // pagination.limit) + 1
    total_pages = math.ceil(total / pagination.limit) if total > 0 else 1
    
    return PQRSPaginatedResponse(
        items=pqrs_list,
        total=total,
        page=page,
        page_size=pagination.limit,
        total_pages=total_pages
    )


@router.get("/my-pqrs", response_model=PQRSPaginatedResponse, status_code=status.HTTP_200_OK)
async def get_my_pqrs(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene las PQRS creadas por el usuario actual
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    pqrs_list, total = await pqrs_service.get_my_pqrs(
        user_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    page = (pagination.skip // pagination.limit) + 1
    total_pages = math.ceil(total / pagination.limit) if total > 0 else 1
    
    return PQRSPaginatedResponse(
        items=pqrs_list,
        total=total,
        page=page,
        page_size=pagination.limit,
        total_pages=total_pages
    )


@router.get("/assigned-to-me", response_model=PQRSPaginatedResponse, status_code=status.HTTP_200_OK)
async def get_assigned_to_me(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene las PQRS asignadas al usuario actual
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    pqrs_list, total = await pqrs_service.get_assigned_to_me(
        user_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    page = (pagination.skip // pagination.limit) + 1
    total_pages = math.ceil(total / pagination.limit) if total > 0 else 1
    
    return PQRSPaginatedResponse(
        items=pqrs_list,
        total=total,
        page=page,
        page_size=pagination.limit,
        total_pages=total_pages
    )


@router.get("/overdue", response_model=List[PQRSResponse], status_code=status.HTTP_200_OK)
async def get_overdue_pqrs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene todas las PQRS que han excedido su deadline
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    overdue_pqrs = await pqrs_service.get_overdue_pqrs()
    
    return overdue_pqrs


@router.get("/statistics", response_model=PQRSStatistics, status_code=status.HTTP_200_OK)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene estadísticas generales de PQRS
    
    Incluye:
    - Total de PQRS
    - Distribución por tipo
    - Distribución por prioridad
    - Distribución por estado
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    stats = await pqrs_service.get_statistics()
    
    return PQRSStatistics(**stats)


@router.get("/{pqrs_id}", response_model=PQRSResponse, status_code=status.HTTP_200_OK)
async def get_pqrs_by_id(
    pqrs_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtiene el detalle completo de una PQRS por ID
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    pqrs = await pqrs_service.get_pqrs_by_id(pqrs_id)
    
    return pqrs


# =============================================================================
# ENDPOINTS DE CREACIÓN Y MODIFICACIÓN
# =============================================================================

@router.post("", response_model=PQRSResponse, status_code=status.HTTP_201_CREATED)
async def create_pqrs(
    pqrs_data: PQRSCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Crea una nueva PQRS
    
    La PQRS se crea con estado inicial "Recibida" y se genera
    un código único automáticamente.
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    # Convertir enums de strings
    pqrs_type = PQRSType(pqrs_data.type.value)
    priority = Priority(pqrs_data.priority.value)
    
    new_pqrs = await pqrs_service.create_pqrs(
        type=pqrs_type,
        subject=pqrs_data.subject,
        description=pqrs_data.description,
        priority=priority,
        created_by=current_user.id,
        requester_name=pqrs_data.requester_name,
        requester_email=pqrs_data.requester_email,
        requester_phone=pqrs_data.requester_phone,
        assigned_to=pqrs_data.assigned_to,
        deadline_days=pqrs_data.deadline_days
    )
    
    return new_pqrs


@router.put("/{pqrs_id}", response_model=PQRSResponse, status_code=status.HTTP_200_OK)
async def update_pqrs(
    pqrs_id: int,
    pqrs_data: PQRSUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Actualiza una PQRS existente
    
    Solo se actualizan los campos proporcionados (partial update).
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    # Convertir priority si fue proporcionada
    priority_enum = None
    if pqrs_data.priority:
        priority_enum = Priority(pqrs_data.priority.value)
    
    updated_pqrs = await pqrs_service.update_pqrs(
        pqrs_id=pqrs_id,
        subject=pqrs_data.subject,
        description=pqrs_data.description,
        priority=priority_enum,
        requester_name=pqrs_data.requester_name,
        requester_email=pqrs_data.requester_email,
        requester_phone=pqrs_data.requester_phone,
        updated_by=current_user.id
    )
    
    return updated_pqrs


@router.delete("/{pqrs_id}", status_code=status.HTTP_200_OK)
async def delete_pqrs(
    pqrs_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Elimina una PQRS
    
    **IMPORTANTE:** Esta acción no se puede deshacer.
    
    **Requiere:** Usuario autenticado con permisos de eliminación
    """
    pqrs_service = get_pqrs_service(db)
    
    success = await pqrs_service.delete_pqrs(
        pqrs_id=pqrs_id,
        deleted_by=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la PQRS"
        )
    
    return {
        "message": "PQRS eliminada exitosamente",
        "pqrs_id": pqrs_id,
        "success": True
    }


# =============================================================================
# ENDPOINTS DE ACCIONES
# =============================================================================

@router.post("/{pqrs_id}/change-status", response_model=PQRSResponse, status_code=status.HTTP_200_OK)
async def change_status(
    pqrs_id: int,
    request: ChangeStatusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cambia el estado de una PQRS
    
    El cambio queda registrado en el historial con el comentario opcional.
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    updated_pqrs = await pqrs_service.change_status(
        pqrs_id=pqrs_id,
        new_status_id=request.new_status_id,
        changed_by=current_user.id,
        comment=request.comment
    )
    
    return updated_pqrs


@router.post("/{pqrs_id}/assign", response_model=PQRSResponse, status_code=status.HTTP_200_OK)
async def assign_to_user(
    pqrs_id: int,
    request: AssignToUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Asigna una PQRS a un usuario
    
    El usuario asignado será responsable de gestionar la PQRS.
    La asignación queda registrada en el historial.
    
    **Requiere:** Usuario autenticado
    """
    pqrs_service = get_pqrs_service(db)
    
    updated_pqrs = await pqrs_service.assign_to_user(
        pqrs_id=pqrs_id,
        user_id=request.user_id,
        assigned_by=current_user.id
    )
    
    return updated_pqrs


# =============================================================================
# NOTAS DE IMPLEMENTACIÓN
# =============================================================================

"""
PERMISOS RECOMENDADOS:

Para implementar control de acceso más granular, considera:

1. Crear PQRS:
   - Cualquier usuario autenticado

2. Ver PQRS:
   - Creador puede ver sus propias PQRS
   - Asignado puede ver PQRS asignadas
   - Admin/Gestor pueden ver todas

3. Actualizar PQRS:
   - Creador solo puede actualizar si está en estado "Recibida"
   - Asignado puede actualizar en cualquier momento
   - Admin/Gestor pueden actualizar siempre

4. Eliminar PQRS:
   - Solo Admin

5. Cambiar estado:
   - Asignado y Admin/Gestor

6. Asignar:
   - Solo Admin/Gestor

Para implementar esto, usa los decoradores de dependencies.py:
- require_admin()
- require_admin_or_manager()
- PermissionChecker(["gestionar_pqrs"])

Ejemplo:
@router.delete("/{pqrs_id}")
async def delete_pqrs(
    pqrs_id: int,
    current_user: User = Depends(require_admin()),  # ← Solo admin
    db: AsyncSession = Depends(get_async_db)
):
    ...
"""