"""
Repository de PQRS
Sistema PQRS - Equipo Desertados

Maneja todas las operaciones de base de datos para:
- PQRS (Peticiones, Quejas, Reclamos, Sugerencias)
- Historial de cambios de estado
- Asignaciones
- Estadísticas
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.models.pqrs import PQRS, PQRSType, PQRSPriority as Priority
from app.models.pqrs_status import PQRSStatus
from app.models.pqrs_history import PQRSHistory
from app.models.user import User


class PQRSRepository:
    """Repository para operaciones CRUD de PQRS"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # =========================================================================
    # OPERACIONES DE LECTURA
    # =========================================================================
    
    async def get_by_id(self, pqrs_id: int) -> Optional[PQRS]:
        """Obtiene una PQRS por ID con todas sus relaciones"""
        result = await self.db.execute(
            select(PQRS)
            .options(
                selectinload(PQRS.status),
                selectinload(PQRS.creator),
                selectinload(PQRS.assignee),
                selectinload(PQRS.history),
                selectinload(PQRS.attachments),
                selectinload(PQRS.comments)
            )
            .where(PQRS.id == pqrs_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_radicado(self, radicado_number: str) -> Optional[PQRS]:
        """Obtiene una PQRS por su número de radicado único"""
        result = await self.db.execute(
            select(PQRS)
            .options(
                selectinload(PQRS.status),
                selectinload(PQRS.creator),
                selectinload(PQRS.assignee)
            )
            .where(PQRS.radicado_number == radicado_number)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status_id: Optional[int] = None,
        pqrs_type: Optional[PQRSType] = None,
        priority: Optional[Priority] = None,
        assigned_to: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> List[PQRS]:
        """
        Obtiene todas las PQRS con filtros opcionales
        
        Args:
            skip: Registros a saltar (paginación)
            limit: Límite de resultados
            status_id: Filtrar por estado
            pqrs_type: Filtrar por tipo (Petición, Queja, etc.)
            priority: Filtrar por prioridad
            assigned_to: Filtrar por usuario asignado
            created_by: Filtrar por creador
        """
        query = select(PQRS).options(
            selectinload(PQRS.status),
            selectinload(PQRS.creator),
            selectinload(PQRS.assignee)
        )
        
        # Aplicar filtros
        if status_id is not None:
            query = query.where(PQRS.status_id == status_id)
        if pqrs_type is not None:
            query = query.where(PQRS.type == pqrs_type)
        if priority is not None:
            query = query.where(PQRS.priority == priority)
        if assigned_to is not None:
            query = query.where(PQRS.assigned_to == assigned_to)
        if created_by is not None:
            query = query.where(PQRS.user_id == created_by)
        
        # Ordenar y paginar
        query = query.order_by(PQRS.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[PQRS]:
        """
        Busca PQRS por código, asunto o descripción
        """
        search_pattern = f"%{search_term}%"
        
        result = await self.db.execute(
            select(PQRS)
            .options(
                selectinload(PQRS.status),
                selectinload(PQRS.creator)
            )
            .where(
                or_(
                    PQRS.radicado_number.ilike(search_pattern),
                    PQRS.subject.ilike(search_pattern),
                    PQRS.description.ilike(search_pattern)
                )
            )
            .order_by(PQRS.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count(
        self,
        status_id: Optional[int] = None,
        pqrs_type: Optional[PQRSType] = None,
        assigned_to: Optional[int] = None
    ) -> int:
        """Cuenta el total de PQRS con filtros opcionales"""
        query = select(func.count(PQRS.id))
        
        if status_id is not None:
            query = query.where(PQRS.status_id == status_id)
        if pqrs_type is not None:
            query = query.where(PQRS.type == pqrs_type)
        if assigned_to is not None:
            query = query.where(PQRS.assigned_to == assigned_to)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    # =========================================================================
    # OPERACIONES DE ESCRITURA
    # =========================================================================
    
    async def create(self, pqrs: PQRS) -> PQRS:
        """Crea una nueva PQRS"""
        self.db.add(pqrs)
        await self.db.flush()
        await self.db.refresh(pqrs)
        return pqrs
    
    async def update(self, pqrs: PQRS) -> PQRS:
        """Actualiza una PQRS existente"""
        await self.db.flush()
        await self.db.refresh(pqrs)
        return pqrs
    
    async def delete(self, pqrs_id: int) -> bool:
        """Elimina una PQRS"""
        result = await self.db.execute(
            delete(PQRS).where(PQRS.id == pqrs_id)
        )
        return result.rowcount > 0
    
    # =========================================================================
    # OPERACIONES DE ESTADO
    # =========================================================================
    
    async def change_status(
        self,
        pqrs_id: int,
        new_status_id: int,
        changed_by: int,
        comment: Optional[str] = None
    ) -> bool:
        """
        Cambia el estado de una PQRS y registra en historial
        """
        # Obtener PQRS actual
        pqrs = await self.get_by_id(pqrs_id)
        if pqrs is None:
            return False
        
        old_status_id = pqrs.status_id
        
        # Actualizar estado
        pqrs.status_id = new_status_id
        
        # Crear registro en historial
        history = PQRSHistory(
            pqrs_id=pqrs_id,
            old_status_id=old_status_id,
            new_status_id=new_status_id,
            changed_by=changed_by,
            comment=comment
        )
        self.db.add(history)
        
        await self.db.flush()
        return True
    
    async def assign_to_user(
        self,
        pqrs_id: int,
        user_id: int,
        assigned_by: int
    ) -> bool:
        """Asigna una PQRS a un usuario"""
        result = await self.db.execute(
            update(PQRS)
            .where(PQRS.id == pqrs_id)
            .values(assigned_to=user_id)
        )
        
        if result.rowcount > 0:
            # Registrar en historial
            history = PQRSHistory(
                pqrs_id=pqrs_id,
                changed_by=assigned_by,
                comment=f"Asignada al usuario ID {user_id}"
            )
            self.db.add(history)
            await self.db.flush()
        
        return result.rowcount > 0
    
    # =========================================================================
    # ESTADÍSTICAS Y REPORTES
    # =========================================================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de PQRS"""
        
        # Total de PQRS
        total_result = await self.db.execute(
            select(func.count(PQRS.id))
        )
        total = total_result.scalar()
        
        # Por tipo
        type_result = await self.db.execute(
            select(PQRS.type, func.count(PQRS.id))
            .group_by(PQRS.type)
        )
        by_type = {row[0].value: row[1] for row in type_result.all()}
        
        # Por prioridad
        priority_result = await self.db.execute(
            select(PQRS.priority, func.count(PQRS.id))
            .group_by(PQRS.priority)
        )
        by_priority = {row[0].value: row[1] for row in priority_result.all()}
        
        # Por estado
        status_result = await self.db.execute(
            select(PQRSStatus.name, func.count(PQRS.id))
            .join(PQRS, PQRS.status_id == PQRSStatus.id)
            .group_by(PQRSStatus.name)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        return {
            "total": total,
            "by_type": by_type,
            "by_priority": by_priority,
            "by_status": by_status
        }
    
    async def get_overdue_pqrs(self) -> List[PQRS]:
        """Obtiene PQRS que han excedido su deadline"""
        now = datetime.utcnow()
        
        result = await self.db.execute(
            select(PQRS)
            .options(
                selectinload(PQRS.status),
                selectinload(PQRS.assignee)
            )
            .where(
                and_(
                    PQRS.deadline < now,
                    PQRS.status_id.notin_(
                        select(PQRSStatus.id).where(PQRSStatus.is_final == True)
                    )
                )
            )
            .order_by(PQRS.deadline)
        )
        return list(result.scalars().all())
    
    async def get_my_pqrs(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[PQRS]:
        """Obtiene PQRS creadas por un usuario específico"""
        result = await self.db.execute(
            select(PQRS)
            .options(
                selectinload(PQRS.status),
                selectinload(PQRS.assignee)
            )
            .where(PQRS.user_id == user_id)
            .order_by(PQRS.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_assigned_to_me(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[PQRS]:
        """Obtiene PQRS asignadas a un usuario específico"""
        result = await self.db.execute(
            select(PQRS)
            .options(
                selectinload(PQRS.status),
                selectinload(PQRS.creator)
            )
            .where(PQRS.assigned_to == user_id)
            .order_by(PQRS.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


def get_pqrs_repository(db: AsyncSession) -> PQRSRepository:
    """Factory function para obtener instancia del repository"""
    return PQRSRepository(db)