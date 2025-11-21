"""Modelo de historial de cambios de PQRS"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class PQRSHistory(Base):
    """Historial de cambios de estado de una PQRS"""
    __tablename__ = "pqrs_history"
    
    id = Column(Integer, primary_key=True, index=True)
    pqrs_id = Column(Integer, ForeignKey("pqrs.id", ondelete="CASCADE"), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey("pqrs_status.id"), nullable=False)
    comment = Column(Text, nullable=True, comment="Comentario sobre el cambio")
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    pqrs = relationship("PQRS", back_populates="history")
    status = relationship("PQRSStatus", back_populates="history_entries")
    user = relationship("User")
    
    def __repr__(self):
        return f"<PQRSHistory(pqrs_id={self.pqrs_id}, status_id={self.status_id})>"