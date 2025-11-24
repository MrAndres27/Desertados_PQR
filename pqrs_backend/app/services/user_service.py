"""
Servicio de Usuarios
Sistema PQRS - Equipo Desertados

Maneja toda la lógica de negocio para:
- Gestión de usuarios (admin)
- Actualización de perfiles
- Activación/desactivación
- Reseteo de contraseñas
- Estadísticas de usuarios
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.role import Role
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, validate_password_strength


class UserService:
    """Servicio para gestión de usuarios"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio con la sesión de BD
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
        self.user_repo = UserRepository(db)
    
    # =========================================================================
    # OPERACIONES DE CONSULTA
    # =========================================================================
    
    async def get_user_by_id(self, user_id: int) -> User:
        """
        Obtiene un usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado
            
        Raises:
            HTTPException 404: Si no existe
        """
        user = await self.user_repo.get_by_id(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )
        
        return user
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None,
        role_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """
        Lista usuarios con filtros y paginación
        
        Args:
            skip: Registros a saltar
            limit: Límite de resultados
            is_active: Filtrar por estado activo/inactivo
            role_id: Filtrar por rol
            search: Búsqueda en username, email, full_name
            
        Returns:
            Tupla (lista_usuarios, total_count)
        """
        if search:
            users_list = await self.user_repo.search(search, skip, limit)
            total = len(users_list)  # Aproximado para búsqueda
        else:
            users_list = await self.user_repo.get_all(
                skip=skip,
                limit=limit,
                is_active=is_active
            )
            total = await self.user_repo.count(is_active=is_active)
        
        # Filtrar por rol si se especifica
        if role_id is not None:
            users_list = [u for u in users_list if u.role_id == role_id]
        
        return users_list, total
    
    async def get_users_by_role(self, role_id: int) -> List[User]:
        """
        Obtiene todos los usuarios de un rol específico
        
        Args:
            role_id: ID del rol
            
        Returns:
            Lista de usuarios
        """
        return await self.user_repo.get_by_role(role_id)
    
    # =========================================================================
    # OPERACIONES DE MODIFICACIÓN
    # =========================================================================
    
    async def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        role_id: Optional[int] = None
    ) -> User:
        """
        Actualiza información de un usuario
        
        Args:
            user_id: ID del usuario
            email: Nuevo email (opcional)
            full_name: Nuevo nombre completo (opcional)
            phone: Nuevo teléfono (opcional)
            address: Nueva dirección (opcional)
            role_id: Nuevo rol (opcional)
            
        Returns:
            Usuario actualizado
        """
        user = await self.get_user_by_id(user_id)
        
        # Verificar email único si se está cambiando
        if email and email != user.email:
            if await self.user_repo.exists_by_email(email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado"
                )
            user.email = email
        
        # Actualizar campos
        if full_name is not None:
            user.full_name = full_name
        if phone is not None:
            user.phone = phone
        if address is not None:
            user.address = address
        if role_id is not None:
            # Verificar que el rol existe
            result = await self.db.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Rol con ID {role_id} no encontrado"
                )
            user.role_id = role_id
        
        updated_user = await self.user_repo.update(user)
        await self.db.commit()
        
        return updated_user
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Elimina un usuario (soft delete si es posible)
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se eliminó correctamente
        """
        # Verificar que existe
        await self.get_user_by_id(user_id)
        
        # Eliminar
        success = await self.user_repo.delete(user_id)
        await self.db.commit()
        
        return success
    
    # =========================================================================
    # GESTIÓN DE ESTADO
    # =========================================================================
    
    async def activate_user(self, user_id: int) -> User:
        """
        Activa un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario activado
        """
        success = await self.user_repo.activate(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )
        
        await self.db.commit()
        
        # Obtener usuario actualizado
        user = await self.get_user_by_id(user_id)
        
        return user
    
    async def deactivate_user(self, user_id: int) -> User:
        """
        Desactiva un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario desactivado
        """
        success = await self.user_repo.deactivate(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )
        
        await self.db.commit()
        
        # Obtener usuario actualizado
        user = await self.get_user_by_id(user_id)
        
        return user
    
    # =========================================================================
    # GESTIÓN DE CONTRASEÑA
    # =========================================================================
    
    async def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """
        Resetea la contraseña de un usuario (solo admin)
        
        Args:
            user_id: ID del usuario
            new_password: Nueva contraseña
            
        Returns:
            True si se reseteo correctamente
        """
        # Verificar que el usuario existe
        await self.get_user_by_id(user_id)
        
        # Validar fortaleza de la nueva contraseña
        is_valid, error_message = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Hashear nueva contraseña
        new_password_hash = hash_password(new_password)
        
        # Actualizar
        success = await self.user_repo.update_password(
            user_id=user_id,
            new_password_hash=new_password_hash
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al resetear la contraseña"
            )
        
        await self.db.commit()
        
        return True
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de usuarios
        
        Returns:
            Dict con estadísticas
        """
        # Total de usuarios
        total_users = await self.user_repo.count()
        
        # Usuarios activos
        active_users = await self.user_repo.count(is_active=True)
        
        # Usuarios inactivos
        inactive_users = await self.user_repo.count(is_active=False)
        
        # Usuarios por rol
        result = await self.db.execute(
            select(
                Role.name,
                func.count(User.id).label('count')
            )
            .join(User, User.role_id == Role.id)
            .group_by(Role.name)
        )
        users_by_role = {row.name: row.count for row in result}
        
        # Usuarios creados en el último mes
        from datetime import timedelta
        last_month = datetime.utcnow() - timedelta(days=30)
        result = await self.db.execute(
            select(func.count(User.id))
            .where(User.created_at >= last_month)
        )
        users_last_month = result.scalar() or 0
        
        # Últimos logins (usuarios activos recientemente)
        last_week = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(func.count(User.id))
            .where(User.last_login >= last_week)
        )
        active_last_week = result.scalar() or 0
        
        return {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
            "by_role": users_by_role,
            "created_last_month": users_last_month,
            "active_last_week": active_last_week
        }
    
    # =========================================================================
    # VALIDACIONES
    # =========================================================================
    
    async def validate_username_available(
        self,
        username: str,
        exclude_user_id: Optional[int] = None
    ) -> bool:
        """
        Valida si un username está disponible
        
        Args:
            username: Username a validar
            exclude_user_id: ID de usuario a excluir de la validación (para updates)
            
        Returns:
            True si está disponible
        """
        exists = await self.user_repo.exists_by_username(username)
        
        if not exists:
            return True
        
        # Si se está actualizando, verificar que no sea del mismo usuario
        if exclude_user_id:
            user = await self.user_repo.get_by_username(username)
            return user.id == exclude_user_id
        
        return False
    
    async def validate_email_available(
        self,
        email: str,
        exclude_user_id: Optional[int] = None
    ) -> bool:
        """
        Valida si un email está disponible
        
        Args:
            email: Email a validar
            exclude_user_id: ID de usuario a excluir de la validación (para updates)
            
        Returns:
            True si está disponible
        """
        exists = await self.user_repo.exists_by_email(email)
        
        if not exists:
            return True
        
        # Si se está actualizando, verificar que no sea del mismo usuario
        if exclude_user_id:
            user = await self.user_repo.get_by_email(email)
            return user.id == exclude_user_id
        
        return False


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_user_service(db: AsyncSession) -> UserService:
    """
    Factory function para obtener una instancia del UserService
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de UserService
    """
    return UserService(db)