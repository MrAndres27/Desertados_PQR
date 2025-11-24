"""
Modelo PQRS - El corazón del sistema.
Representa Peticiones, Quejas, Reclamos y Sugerencias.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base

class PQRSType(str, enum.Enum):
    """Tipos de PQRS"""
    PETICION = "peticion"
    QUEJA = "queja"
    RECLAMO = "reclamo"
    SUGERENCIA = "sugerencia"

class PQRSPriority(str, enum.Enum):
    """Prioridades de PQRS"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"  # ← AGREGADO

class SemaphoreColor(str, enum.Enum):
    """Colores de semáforo"""
    VERDE = "verde"
    AMARILLO = "amarillo"
    ROJO = "rojo"

# Alias para compatibilidad con código existente
Priority = PQRSPriority  # ← AGREGADO

class PQRS(Base):
    """
    Modelo principal de PQRS.
    
    Representa una solicitud de Petición, Queja, Reclamo o Sugerencia.
    Incluye información completa de la solicitud, su estado, asignación, etc.
    """
    
    __tablename__ = "pqrs"
    
    # IDs y referencias
    id = Column(Integer, primary_key=True, index=True)
    radicado_number = Column(String(50), unique=True, nullable=False, index=True,
                            comment="Número de radicado único generado automáticamente")
    
    # Tipo y clasificación
    type = Column(SQLEnum(PQRSType), nullable=False, index=True,
                 comment="Tipo: peticion, queja, reclamo, sugerencia")
    priority = Column(SQLEnum(PQRSPriority), nullable=False, default=PQRSPriority.MEDIA,
                     comment="Prioridad: baja, media, alta, critica")  # ← ACTUALIZADO COMENTARIO
    
    # Contenido
    subject = Column(String(255), nullable=False,
                    comment="Asunto o título de la PQRS")
    description = Column(Text, nullable=False,
                        comment="Descripción detallada de la solicitud")
    
    # Estado y semaforización
    status_id = Column(Integer, ForeignKey("pqrs_status.id"), nullable=False, index=True)
    semaphore_color = Column(SQLEnum(SemaphoreColor), nullable=False, default=SemaphoreColor.VERDE,
                            comment="Color del semáforo: verde, amarillo, rojo")
    
    # Relaciones con usuarios
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True,
                    comment="ID del usuario que creó la PQRS")
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True, index=True,
                        comment="ID del usuario asignado para atender la PQRS")
    
    # Fechas importantes
    due_date = Column(DateTime, nullable=False,
                     comment="Fecha límite para atender (calculada según tipo de PQRS)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True,
                        comment="Fecha en que se resolvió la PQRS")
    
    # Relaciones
    status = relationship("PQRSStatus", back_populates="pqrs")
    creator = relationship("User", foreign_keys=[user_id], back_populates="pqrs_created")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="pqrs_assigned")
    history = relationship("PQRSHistory", back_populates="pqrs", cascade="all, delete-orphan")
    files = relationship("FileAttachment", back_populates="pqrs", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="pqrs", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PQRS(id={self.id}, radicado='{self.radicado_number}', type='{self.type}')>"
    
    def __str__(self):
        return f"{self.radicado_number} - {self.subject}"
    
    @property
    def is_overdue(self) -> bool:
        """Verifica si la PQRS está vencida"""
        if self.resolved_at:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def days_remaining(self) -> int:
        """Días restantes para vencimiento"""
        if self.resolved_at:
            return 0
        delta = self.due_date - datetime.utcnow()
        return max(0, delta.days)