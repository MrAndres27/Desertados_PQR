"""
Repository de Usuarios
Sistema PQRS - Equipo Desertados

Maneja todas las operaciones de base de datos relacionadas con usuarios.
Implementa el patrón Repository para separar la lógica de acceso a datos.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import Role


class UserRepository:
    """Repository para operaciones CRUD de usuarios"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el repository con una sesión de base de datos
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
    
    # =========================================================================
    # OPERACIONES DE LECTURA
    # =========================================================================
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por su ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado o None si no existe
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Obtiene un usuario por su username
        
        Args:
            username: Username del usuario
            
        Returns:
            Usuario encontrado o None
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role).selectinload(Role.permissions))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role).selectinload(Role.permissions))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        Obtiene todos los usuarios con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            is_active: Filtrar por usuarios activos/inactivos (opcional)
            
        Returns:
            Lista de usuarios
        """
        query = select(User).options(
            selectinload(User.role)
        )
        
        # Filtrar por estado activo si se especifica
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        # Ordenar y paginar
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[User]:
        """
        Busca usuarios por nombre, username o email
        
        Args:
            search_term: Término de búsqueda
            skip: Registros a saltar
            limit: Límite de resultados
            
        Returns:
            Lista de usuarios que coinciden con la búsqueda
        """
        search_pattern = f"%{search_term}%"
        
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            )
            .order_by(User.username)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count(self, is_active: Optional[bool] = None) -> int:
        """
        Cuenta el total de usuarios
        
        Args:
            is_active: Filtrar por activos/inactivos (opcional)
            
        Returns:
            Número total de usuarios
        """
        query = select(func.count(User.id))
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def exists_by_username(self, username: str) -> bool:
        """
        Verifica si existe un usuario con el username dado
        
        Args:
            username: Username a verificar
            
        Returns:
            True si existe, False si no
        """
        result = await self.db.execute(
            select(func.count(User.id)).where(User.username == username)
        )
        count = result.scalar()
        return count > 0
    
    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe, False si no
        """
        result = await self.db.execute(
            select(func.count(User.id)).where(User.email == email)
        )
        count = result.scalar()
        return count > 0
    
    # =========================================================================
    # OPERACIONES DE ESCRITURA
    # =========================================================================
    
    async def create(self, user: User) -> User:
        """
        Crea un nuevo usuario en la base de datos
        
        Args:
            user: Instancia de User a crear
            
        Returns:
            Usuario creado con su ID asignado
        """
        self.db.add(user)
        await self.db.flush()  # Para obtener el ID sin hacer commit
        await self.db.refresh(user)  # Refrescar con las relaciones
        return user
    
    async def update(self, user: User) -> User:
        """
        Actualiza un usuario existente
        
        Args:
            user: Usuario con los cambios a guardar
            
        Returns:
            Usuario actualizado
        """
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> bool:
        """
        Elimina un usuario de la base de datos
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        result = await self.db.execute(
            delete(User).where(User.id == user_id)
        )
        return result.rowcount > 0
    
    async def activate(self, user_id: int) -> bool:
        """
        Activa un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se activó correctamente
        """
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=True)
        )
        return result.rowcount > 0
    
    async def deactivate(self, user_id: int) -> bool:
        """
        Desactiva un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se desactivó correctamente
        """
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        return result.rowcount > 0
    
    # =========================================================================
    # OPERACIONES ESPECIALES
    # =========================================================================
    
    async def get_by_role(self, role_id: int) -> List[User]:
        """
        Obtiene todos los usuarios con un rol específico
        
        Args:
            role_id: ID del rol
            
        Returns:
            Lista de usuarios con ese rol
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.role_id == role_id)
            .order_by(User.username)
        )
        return list(result.scalars().all())
    
    async def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """
        Actualiza la contraseña de un usuario
        
        Args:
            user_id: ID del usuario
            new_password_hash: Hash de la nueva contraseña
            
        Returns:
            True si se actualizó correctamente
        """
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=new_password_hash)
        )
        return result.rowcount > 0
    
    async def update_last_login(self, user_id: int) -> bool:
        """
        Actualiza la fecha de último login del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se actualizó correctamente
        """
        from datetime import datetime
        
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        return result.rowcount > 0


# =============================================================================
# FUNCIÓN HELPER PARA OBTENER EL REPOSITORY
# =============================================================================

def get_user_repository(db: AsyncSession) -> UserRepository:
    """
    Factory function para obtener una instancia del UserRepository
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de UserRepository
        
    Uso en FastAPI:
        async def some_endpoint(
            user_repo: UserRepository = Depends(
                lambda db=Depends(get_async_db): get_user_repository(db)
            )
        ):
            user = await user_repo.get_by_id(1)
    """
    return UserRepository(db)