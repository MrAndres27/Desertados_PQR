"""Modelo de logs de auditoría"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditLog(Base):
    """Logs de auditoría del sistema"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True, comment="Acción: CREATE, UPDATE, DELETE, LOGIN")
    entity = Column(String(50), nullable=False, comment="Entidad afectada: PQRS, User, etc.")
    entity_id = Column(Integer, nullable=True, comment="ID de la entidad afectada")
    old_value = Column(Text, nullable=True, comment="Valor anterior (JSON)")
    new_value = Column(Text, nullable=True, comment="Valor nuevo (JSON)")
    ip_address = Column(String(45), nullable=True, comment="IP del usuario")
    user_agent = Column(String(255), nullable=True, comment="User agent del navegador")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity}')>"
