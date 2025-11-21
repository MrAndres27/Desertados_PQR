"""
Servicio de Autenticación
Sistema PQRS - Equipo Desertados

Maneja toda la lógica de negocio relacionada con:
- Login y generación de tokens
- Registro de nuevos usuarios
- Refresh de tokens
- Cambio de contraseña
"""

from typing import Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.role import Role
from app.repositories.user_repository import UserRepository
from app.core.security import (
    verify_password,
    hash_password,
    create_token_pair,
    verify_token,
    validate_password_strength
)


class AuthService:
    """Servicio de autenticación y gestión de usuarios"""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio con la sesión de BD
        
        Args:
            db: Sesión asíncrona de SQLAlchemy
        """
        self.db = db
        self.user_repo = UserRepository(db)
    
    # =========================================================================
    # AUTENTICACIÓN
    # =========================================================================
    
    async def login(
        self,
        username: str,
        password: str
    ) -> Dict[str, str]:
        """
        Autentica un usuario y genera tokens JWT
        
        Args:
            username: Username o email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Dict con access_token, refresh_token y token_type
            
        Raises:
            HTTPException 401: Si las credenciales son incorrectas
            HTTPException 403: Si el usuario está inactivo
        """
        # Buscar usuario por username o email
        user = await self.user_repo.get_by_username(username)
        if user is None:
            user = await self.user_repo.get_by_email(username)
        
        # Verificar que el usuario existe
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar contraseña
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo. Contacte al administrador."
            )
        
        # Actualizar fecha de último login
        await self.user_repo.update_last_login(user.id)
        await self.db.commit()
        
        # Preparar datos para el token
        user_data = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.name,
            "role_id": user.role.id,
            "permissions": [p.name for p in user.role.permissions]
        }
        
        # Generar tokens
        tokens = create_token_pair(user_data)
        
        return tokens
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Dict[str, str]:
        """
        Genera un nuevo access token usando un refresh token válido
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            Dict con nuevo access_token
            
        Raises:
            HTTPException 401: Si el refresh token es inválido
        """
        # Verificar refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Obtener usuario
        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)
        
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Preparar datos para nuevo token
        user_data = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.name,
            "role_id": user.role.id,
            "permissions": [p.name for p in user.role.permissions]
        }
        
        # Generar nuevo par de tokens
        tokens = create_token_pair(user_data)
        
        return tokens
    
    # =========================================================================
    # REGISTRO
    # =========================================================================
    
    async def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        document_type: str,
        document_number: str,
        phone: Optional[str] = None,
        address: Optional[str] = None
    ) -> User:
        """
        Registra un nuevo usuario en el sistema
        
        Args:
            username: Username único
            email: Email único
            password: Contraseña (se hasheará)
            full_name: Nombre completo
            document_type: Tipo de documento (CC, CE, etc.)
            document_number: Número de documento
            phone: Teléfono (opcional)
            address: Dirección (opcional)
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException 400: Si los datos son inválidos o ya existen
        """
        # Validar contraseña
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Verificar que username no existe
        if await self.user_repo.exists_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El username ya está en uso"
            )
        
        # Verificar que email no existe
        if await self.user_repo.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Obtener rol por defecto (Usuario)
        from sqlalchemy import select as sql_select
        result = await self.db.execute(
            sql_select(Role).where(Role.name == "Usuario")
        )
        default_role = result.scalar_one_or_none()
        
        if default_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en configuración del sistema: rol por defecto no existe"
            )
        
        # Hashear contraseña
        password_hash = hash_password(password)
        
        # Crear usuario
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            document_type=document_type,
            document_number=document_number,
            phone=phone,
            address=address,
            role_id=default_role.id,
            is_active=True  # Los usuarios nuevos están activos por defecto
        )
        
        # Guardar en base de datos
        created_user = await self.user_repo.create(new_user)
        await self.db.commit()
        await self.db.refresh(created_user)
        
        return created_user
    
    # =========================================================================
    # GESTIÓN DE CONTRASEÑA
    # =========================================================================
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Cambia la contraseña de un usuario
        
        Args:
            user_id: ID del usuario
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            True si se cambió correctamente
            
        Raises:
            HTTPException 400: Si la contraseña actual es incorrecta
            HTTPException 404: Si el usuario no existe
        """
        # Obtener usuario
        user = await self.user_repo.get_by_id(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar contraseña actual
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )
        
        # Validar nueva contraseña
        is_valid, error_message = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Hashear nueva contraseña
        new_password_hash = hash_password(new_password)
        
        # Actualizar contraseña
        success = await self.user_repo.update_password(user_id, new_password_hash)
        
        if success:
            await self.db.commit()
        
        return success
    
    async def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """
        Restablece la contraseña de un usuario (solo admin)
        
        Args:
            user_id: ID del usuario
            new_password: Nueva contraseña
            
        Returns:
            True si se cambió correctamente
            
        Raises:
            HTTPException 400: Si la nueva contraseña no es válida
            HTTPException 404: Si el usuario no existe
        """
        # Verificar que el usuario existe
        user = await self.user_repo.get_by_id(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Validar nueva contraseña
        is_valid, error_message = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Hashear nueva contraseña
        new_password_hash = hash_password(new_password)
        
        # Actualizar contraseña
        success = await self.user_repo.update_password(user_id, new_password_hash)
        
        if success:
            await self.db.commit()
        
        return success
    
    # =========================================================================
    # VALIDACIONES
    # =========================================================================
    
    async def validate_username_available(self, username: str) -> bool:
        """
        Valida si un username está disponible
        
        Args:
            username: Username a verificar
            
        Returns:
            True si está disponible, False si ya existe
        """
        return not await self.user_repo.exists_by_username(username)
    
    async def validate_email_available(self, email: str) -> bool:
        """
        Valida si un email está disponible
        
        Args:
            email: Email a verificar
            
        Returns:
            True si está disponible, False si ya existe
        """
        return not await self.user_repo.exists_by_email(email)


# =============================================================================
# FUNCIÓN HELPER
# =============================================================================

def get_auth_service(db: AsyncSession) -> AuthService:
    """
    Factory function para obtener una instancia del AuthService
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Instancia de AuthService
    """
    return AuthService(db)