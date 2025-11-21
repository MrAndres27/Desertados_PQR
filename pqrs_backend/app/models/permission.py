"""
Modelo de Permiso del sistema.
Define permisos granulares: crear_pqrs, editar_pqrs, ver_dashboard, etc.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.role import role_permissions

class Permission(Base):
    """
    Modelo de Permiso.
    
    Define permisos granulares que se asignan a roles.
    Ejemplos: crear_pqrs, editar_pqrs, eliminar_pqrs, ver_dashboard, gestionar_usuarios.
    """
    
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True,
                  comment="Nombre único del permiso (ej: crear_pqrs)")
    description = Column(String(255), nullable=True,
                        comment="Descripción de qué permite este permiso")
    module = Column(String(50), nullable=False, index=True,
                   comment="Módulo al que pertenece (pqrs, users, dashboard, etc.)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', module='{self.module}')>"
    
    def __str__(self):
        return self.name
