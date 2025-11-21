"""
Modelo de Usuario del sistema.

Define la tabla 'users' en la base de datos con todos los campos
necesarios para la gestión de usuarios y autenticación.

Autor: Equipo Desertados PQRS
Fecha: 2025
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    Modelo de Usuario.
    
    Representa a los usuarios del sistema (administradores, gestores,
    supervisores y usuarios finales que crean PQRS).
    
    Attributes:
        id: Identificador único del usuario
        username: Nombre de usuario único para login
        email: Correo electrónico único
        hashed_password: Contraseña hasheada con bcrypt (nunca en texto plano)
        full_name: Nombre completo del usuario
        phone: Teléfono de contacto (opcional)
        is_active: Si el usuario está activo o deshabilitado
        is_superuser: Si el usuario tiene permisos de superadministrador
        role_id: ID del rol asignado (Administrador, Gestor, etc.)
        created_at: Fecha de creación del usuario
        updated_at: Fecha de última actualización
        
    Relationships:
        role: Relación con la tabla Role (Many-to-One)
        pqrs_created: PQRS creadas por este usuario (One-to-Many)
        pqrs_assigned: PQRS asignadas a este usuario (One-to-Many)
        notifications: Notificaciones del usuario (One-to-Many)
        audit_logs: Logs de auditoría del usuario (One-to-Many)
    """
    
    # Nombre de la tabla en la base de datos
    __tablename__ = "users"
    
    # =========================================================================
    # COLUMNAS PRINCIPALES
    # =========================================================================
    
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="ID único del usuario (auto-incremental)"
    )
    
    username = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Nombre de usuario único para login"
    )
    
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Correo electrónico único del usuario"
    )
    
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Contraseña hasheada con bcrypt (NUNCA guardar en texto plano)"
    )
    
    full_name = Column(
        String(100),
        nullable=False,
        comment="Nombre completo del usuario"
    )
    
    phone = Column(
        String(20),
        nullable=True,
        comment="Teléfono de contacto (opcional)"
    )
    
    # =========================================================================
    # COLUMNAS DE ESTADO
    # =========================================================================
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Si el usuario está activo. False = deshabilitado"
    )
    
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Si es superadministrador (acceso total al sistema)"
    )
    
    # =========================================================================
    # RELACIONES (FOREIGN KEYS)
    # =========================================================================
    
    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="ID del rol asignado (Administrador, Gestor, Supervisor, Usuario)"
    )
    
    # =========================================================================
    # COLUMNAS DE AUDITORÍA (TIMESTAMPS)
    # =========================================================================
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Fecha y hora de creación del usuario"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Fecha y hora de última actualización"
    )
    
    # =========================================================================
    # RELACIONES (ORM Relationships)
    # =========================================================================
    
    # Relación con Role (Many-to-One: muchos usuarios pueden tener el mismo rol)
    role = relationship(
        "Role",
        back_populates="users",
        lazy="joined"  # Cargar el rol automáticamente al cargar el usuario
    )
    
    # Relación con PQRS creadas por este usuario (One-to-Many)
    pqrs_created = relationship(
        "PQRS",
        back_populates="creator",
        foreign_keys="PQRS.user_id",
        cascade="all, delete-orphan"  # Si se elimina el usuario, eliminar sus PQRS
    )
    
    # Relación con PQRS asignadas a este usuario (One-to-Many)
    pqrs_assigned = relationship(
        "PQRS",
        back_populates="assignee",
        foreign_keys="PQRS.assigned_to"
    )
    
    # Relación con Notificaciones (One-to-Many)
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Relación con Logs de Auditoría (One-to-Many)
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # =========================================================================
    # MÉTODOS ESPECIALES
    # =========================================================================
    
    def __repr__(self) -> str:
        """
        Representación del objeto User para debugging.
        
        Returns:
            str: Representación legible del usuario
            
        Ejemplo:
            >>> user = User(username="juan", email="juan@example.com")
            >>> print(user)
            <User(id=1, username='juan', email='juan@example.com')>
        """
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def __str__(self) -> str:
        """
        Conversión a string del usuario.
        
        Returns:
            str: Nombre de usuario
            
        Ejemplo:
            >>> user = User(username="juan")
            >>> str(user)
            'juan'
        """
        return self.username
    
    # =========================================================================
    # MÉTODOS DE UTILIDAD
    # =========================================================================
    
    @property
    def is_admin(self) -> bool:
        """
        Verifica si el usuario es administrador.
        
        Returns:
            bool: True si es superusuario o tiene rol de Administrador
            
        Ejemplo:
            >>> if user.is_admin:
            ...     print("Usuario tiene permisos de administrador")
        """
        return self.is_superuser or (self.role and self.role.name == "Administrador")
    
    @property
    def can_manage_users(self) -> bool:
        """
        Verifica si el usuario puede gestionar otros usuarios.
        
        Returns:
            bool: True si puede gestionar usuarios
        """
        allowed_roles = ["Administrador", "Gestor"]
        return self.is_superuser or (self.role and self.role.name in allowed_roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """
        Verifica si el usuario tiene un permiso específico.
        
        Args:
            permission_name: Nombre del permiso a verificar
            
        Returns:
            bool: True si tiene el permiso, False si no
            
        Ejemplo:
            >>> if user.has_permission("crear_pqrs"):
            ...     print("Usuario puede crear PQRS")
        """
        if self.is_superuser:
            return True
        
        if not self.role:
            return False
        
        return any(
            perm.name == permission_name
            for perm in self.role.permissions
        )
    
    def to_dict(self) -> dict:
        """
        Convierte el usuario a diccionario (sin contraseña).
        
        Útil para serialización y APIs.
        IMPORTANTE: No incluye hashed_password por seguridad.
        
        Returns:
            dict: Diccionario con los datos del usuario
            
        Ejemplo:
            >>> user_dict = user.to_dict()
            >>> print(user_dict)
            {'id': 1, 'username': 'juan', 'email': 'juan@example.com', ...}
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "role_id": self.role_id,
            "role_name": self.role.name if self.role else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# =============================================================================
# ÍNDICES ADICIONALES (Para optimizar queries)
# =============================================================================

# SQLAlchemy creará estos índices automáticamente por los parámetros index=True
# Pero si necesitas índices compuestos, se definen así:

# from sqlalchemy import Index
# Index('idx_user_email_active', User.email, User.is_active)
# Index('idx_user_role_active', User.role_id, User.is_active)