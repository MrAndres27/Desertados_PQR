"""
Modelo de Rol del sistema.
Define los roles de usuario: Administrador, Gestor, Supervisor, Usuario.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

# Tabla intermedia para Many-to-Many entre Role y Permission
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    comment="Tabla intermedia: relación Many-to-Many entre roles y permisos"
)

class Role(Base):
    """
    Modelo de Rol.
    
    Define los roles del sistema que determinan qué puede hacer cada usuario.
    Ejemplos: Administrador, Gestor, Supervisor, Usuario.
    """
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True, 
                  comment="Nombre del rol (Administrador, Gestor, Supervisor, Usuario)")
    description = Column(String(255), nullable=True,
                        comment="Descripción del rol y sus funciones")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"
    
    def __str__(self):
        return self.name
