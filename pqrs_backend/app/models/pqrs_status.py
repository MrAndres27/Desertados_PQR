"""
Modelo de Estado de PQRS.
Define los estados posibles: Recibida, En Proceso, Resuelta, Cerrada, Cancelada.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base

class PQRSStatus(Base):
    """
    Modelo de Estado de PQRS.
    
    Define los estados del ciclo de vida de una PQRS.
    Estados típicos: Recibida → En Proceso → Resuelta → Cerrada
    """
    
    __tablename__ = "pqrs_status"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True,
                  comment="Nombre del estado (Recibida, En Proceso, Resuelta, etc.)")
    description = Column(String(255), nullable=True,
                        comment="Descripción del estado")
    order = Column(Integer, nullable=False, default=0,
                  comment="Orden de visualización (para ordenar estados)")
    is_final = Column(Integer, default=0,
                     comment="1 si es un estado final (Cerrada, Cancelada), 0 si no")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    pqrs = relationship("PQRS", back_populates="status")
    history_entries = relationship("PQRSHistory", back_populates="status")
    
    def __repr__(self):
        return f"<PQRSStatus(id={self.id}, name='{self.name}', order={self.order})>"
    
    def __str__(self):
        return self.name

