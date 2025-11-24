"""
Servicio de PQRS
Sistema PQRS - Equipo Desertados

Maneja toda la lógica de negocio para:
- Crear, leer, actualizar y eliminar PQRS
- Asignación de PQRS a usuarios
- Cambio de estados con historial
- Gestión de archivos adjuntos
- Estadísticas y reportes
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pqrs import PQRS, PQRSType, PQRSPriority as Priority
from app.models.pqrs_status import PQRSStatus
from app.models.pqrs_history import PQRSHistory
from app.models.user import User
from app.repositories.pqrs_repository import PQRSRepository


class PQRSService:
    """Servicio para gestión de PQRS"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio con la sesión de BD
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
        self.pqrs_repo = PQRSRepository(db)
    
    # =========================================================================
    # OPERACIONES CRUD
    # =========================================================================
    
    async def create_pqrs(
        self,
        type: PQRSType,
        subject: str,
        description: str,
        priority: Priority,
        created_by: int,
        requester_name: Optional[str] = None,
        requester_email: Optional[str] = None,
        requester_phone: Optional[str] = None,
        assigned_to: Optional[int] = None,
        deadline_days: int = 15
    ) -> PQRS:
        """
        Crea una nueva PQRS
        
        Args:
            type: Tipo (Petición, Queja, Reclamo, Sugerencia)
            subject: Asunto
            description: Descripción detallada
            priority: Prioridad (Baja, Media, Alta, Crítica)
            created_by: ID del usuario que crea
            requester_name: Nombre del solicitante (opcional)
            requester_email: Email del solicitante (opcional)
            requester_phone: Teléfono del solicitante (opcional)
            assigned_to: ID del usuario asignado (opcional)
            deadline_days: Días para resolver (default 15)
            
        Returns:
            PQRS creada
        """
        # Obtener estado inicial "Recibida"
        result = await self.db.execute(
            select(PQRSStatus)
            .where(PQRSStatus.name == "Recibida")
            .where(PQRSStatus.order == 1)
        )
        initial_status = result.scalar_one_or_none()
        
        if initial_status is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Estado inicial 'Recibida' no encontrado. Inicializa la BD."
            )
        
        # Generar código único (formato: PQRS-YYYYMMDD-XXXX)
        radicado_number = await self._generate_unique_code()
        
        # Calcular deadline
        due_date = datetime.utcnow() + timedelta(days=deadline_days)
        
        # Crear PQRS
        new_pqrs = PQRS(
            radicado_number=radicado_number,
            type=type,
            subject=subject,
            description=description,
            priority=priority,
            status_id=initial_status.id,
            requester_name=requester_name,
            requester_email=requester_email,
            requester_phone=requester_phone,
            user_id=created_by,
            assigned_to=assigned_to,
            due_date=due_date
        )
        
        # Guardar en BD
        created_pqrs = await self.pqrs_repo.create(new_pqrs)
        await self.db.commit()
        await self.db.refresh(created_pqrs)
        
        # Crear registro inicial en historial
        history = PQRSHistory(
            pqrs_id=created_pqrs.id,
            old_status_id=None,
            new_status_id=initial_status.id,
            changed_by=created_by,
            comment="PQRS creada"
        )
        self.db.add(history)
        await self.db.commit()
        
        return created_pqrs
    
    async def get_pqrs_by_id(self, pqrs_id: int) -> PQRS:
        """
        Obtiene una PQRS por ID
        
        Args:
            pqrs_id: ID de la PQRS
            
        Returns:
            PQRS encontrada
            
        Raises:
            HTTPException 404: Si no existe
        """
        pqrs = await self.pqrs_repo.get_by_id(pqrs_id)
        
        if pqrs is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PQRS con ID {pqrs_id} no encontrada"
            )
        
        return pqrs
    
    
    async def list_pqrs(
        self,
        skip: int = 0,
        limit: int = 20,
        status_id: Optional[int] = None,
        pqrs_type: Optional[PQRSType] = None,
        priority: Optional[Priority] = None,
        assigned_to: Optional[int] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None
    ) -> tuple[List[PQRS], int]:
        """
        Lista PQRS con filtros y paginación
        
        Args:
            skip: Registros a saltar
            limit: Límite de resultados
            status_id: Filtrar por estado
            pqrs_type: Filtrar por tipo
            priority: Filtrar por prioridad
            assigned_to: Filtrar por asignado
            created_by: Filtrar por creador
            search: Búsqueda en código/asunto/descripción
            
        Returns:
            Tupla (lista_pqrs, total_count)
        """
        if search:
            pqrs_list = await self.pqrs_repo.search(search, skip, limit)
            total = len(pqrs_list)  # Aproximado para búsqueda
        else:
            pqrs_list = await self.pqrs_repo.get_all(
                skip=skip,
                limit=limit,
                status_id=status_id,
                pqrs_type=pqrs_type,
                priority=priority,
                assigned_to=assigned_to,
                created_by=created_by
            )
            total = await self.pqrs_repo.count(
                status_id=status_id,
                pqrs_type=pqrs_type,
                assigned_to=assigned_to
            )
        
        return pqrs_list, total
    
    async def update_pqrs(
        self,
        pqrs_id: int,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        requester_name: Optional[str] = None,
        requester_email: Optional[str] = None,
        requester_phone: Optional[str] = None,
        updated_by: int = None
    ) -> PQRS:
        """
        Actualiza una PQRS existente
        
        Args:
            pqrs_id: ID de la PQRS
            subject: Nuevo asunto (opcional)
            description: Nueva descripción (opcional)
            priority: Nueva prioridad (opcional)
            requester_name: Nuevo nombre solicitante (opcional)
            requester_email: Nuevo email solicitante (opcional)
            requester_phone: Nuevo teléfono solicitante (opcional)
            updated_by: ID del usuario que actualiza
            
        Returns:
            PQRS actualizada
        """
        pqrs = await self.get_pqrs_by_id(pqrs_id)
        
        # Actualizar solo los campos proporcionados
        if subject is not None:
            pqrs.subject = subject
        if description is not None:
            pqrs.description = description
        if priority is not None:
            pqrs.priority = priority
        if requester_name is not None:
            pqrs.requester_name = requester_name
        if requester_email is not None:
            pqrs.requester_email = requester_email
        if requester_phone is not None:
            pqrs.requester_phone = requester_phone
        
        updated_pqrs = await self.pqrs_repo.update(pqrs)
        await self.db.commit()
        
        # Registrar en historial
        if updated_by:
            history = PQRSHistory(
                pqrs_id=pqrs_id,
                changed_by=updated_by,
                comment="PQRS actualizada"
            )
            self.db.add(history)
            await self.db.commit()
        
        return updated_pqrs
    
    async def delete_pqrs(self, pqrs_id: int, deleted_by: int) -> bool:
        """
        Elimina una PQRS (soft delete si es posible, o hard delete)
        
        Args:
            pqrs_id: ID de la PQRS
            deleted_by: ID del usuario que elimina
            
        Returns:
            True si se eliminó correctamente
        """
        # Verificar que existe
        await self.get_pqrs_by_id(pqrs_id)
        
        # Registrar en historial antes de eliminar
        history = PQRSHistory(
            pqrs_id=pqrs_id,
            changed_by=deleted_by,
            comment="PQRS eliminada"
        )
        self.db.add(history)
        await self.db.commit()
        
        # Eliminar
        success = await self.pqrs_repo.delete(pqrs_id)
        await self.db.commit()
        
        return success
    
    # =========================================================================
    # GESTIÓN DE ESTADOS
    # =========================================================================
    
    async def change_status(
        self,
        pqrs_id: int,
        new_status_id: int,
        changed_by: int,
        comment: Optional[str] = None
    ) -> PQRS:
        """
        Cambia el estado de una PQRS
        
        Args:
            pqrs_id: ID de la PQRS
            new_status_id: ID del nuevo estado
            changed_by: ID del usuario que cambia
            comment: Comentario sobre el cambio (opcional)
            
        Returns:
            PQRS actualizada
        """
        pqrs = await self.get_pqrs_by_id(pqrs_id)
        
        # Verificar que el nuevo estado existe
        result = await self.db.execute(
            select(PQRSStatus).where(PQRSStatus.id == new_status_id)
        )
        new_status = result.scalar_one_or_none()
        
        if new_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {new_status_id} no encontrado"
            )
        
        # Cambiar estado
        success = await self.pqrs_repo.change_status(
            pqrs_id=pqrs_id,
            new_status_id=new_status_id,
            changed_by=changed_by,
            comment=comment
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al cambiar el estado"
            )
        
        await self.db.commit()
        
        # Obtener PQRS actualizada
        updated_pqrs = await self.get_pqrs_by_id(pqrs_id)
        
        return updated_pqrs
    
    # =========================================================================
    # ASIGNACIÓN
    # =========================================================================
    
    async def assign_to_user(
        self,
        pqrs_id: int,
        user_id: int,
        assigned_by: int
    ) -> PQRS:
        """
        Asigna una PQRS a un usuario
        
        Args:
            pqrs_id: ID de la PQRS
            user_id: ID del usuario a asignar
            assigned_by: ID del usuario que asigna
            
        Returns:
            PQRS actualizada
        """
        # Verificar que la PQRS existe
        pqrs = await self.get_pqrs_by_id(pqrs_id)
        
        # Verificar que el usuario existe
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )
        
        # Asignar
        success = await self.pqrs_repo.assign_to_user(
            pqrs_id=pqrs_id,
            user_id=user_id,
            assigned_by=assigned_by
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al asignar PQRS"
            )
        
        await self.db.commit()
        
        # Obtener PQRS actualizada
        updated_pqrs = await self.get_pqrs_by_id(pqrs_id)
        
        return updated_pqrs
    
    # =========================================================================
    # CONSULTAS ESPECIALES
    # =========================================================================
    
    async def get_my_pqrs(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[PQRS], int]:
        """
        Obtiene las PQRS creadas por un usuario
        
        Args:
            user_id: ID del usuario
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Tupla (lista_pqrs, total_count)
        """
        pqrs_list = await self.pqrs_repo.get_my_pqrs(user_id, skip, limit)
        total = await self.pqrs_repo.count(created_by=user_id)
        
        return pqrs_list, total
    
    async def get_assigned_to_me(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[PQRS], int]:
        """
        Obtiene las PQRS asignadas a un usuario
        
        Args:
            user_id: ID del usuario
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Tupla (lista_pqrs, total_count)
        """
        pqrs_list = await self.pqrs_repo.get_assigned_to_me(user_id, skip, limit)
        total = await self.pqrs_repo.count(assigned_to=user_id)
        
        return pqrs_list, total
    
    async def get_overdue_pqrs(self) -> List[PQRS]:
        """
        Obtiene PQRS que han excedido su deadline
        
        Returns:
            Lista de PQRS vencidas
        """
        return await self.pqrs_repo.get_overdue_pqrs()
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de PQRS
        
        Returns:
            Dict con estadísticas
        """
        return await self.pqrs_repo.get_statistics()
    
    # =========================================================================
    # FUNCIONES AUXILIARES
    # =========================================================================
    
    async def _generate_unique_code(self) -> str:
        """
        Genera un código único para PQRS
        
        Formato: PQRS-YYYYMMDD-XXXX
        Ejemplo: PQRS-20241121-0001
        
        Returns:
            Código único
        """
        from sqlalchemy import func
        
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"PQRS-{today}"
        
        # Contar PQRS de hoy
        result = await self.db.execute(
            select(func.count(PQRS.id))
            .where(PQRS.radicado_number.like(f"{prefix}%"))
        )
        count = result.scalar() or 0
        
        # Generar código
        sequence = str(count + 1).zfill(4)
        radicado_number = f"{prefix}-{sequence}"
        
        # Verificar que no existe (por si acaso)
        result = await self.db.execute(
            select(PQRS).where(PQRS.radicado_number == radicado_number)
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Si existe, incrementar secuencia
            sequence = str(count + 2).zfill(4)
            radicado_number = f"{prefix}-{sequence}"
        
        return radicado_number


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_pqrs_service(db: AsyncSession) -> PQRSService:
    """
    Factory function para obtener una instancia del PQRSService
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de PQRSService
    """
    return PQRSService(db)