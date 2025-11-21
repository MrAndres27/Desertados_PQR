"""Modelo de archivos adjuntos"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class FileAttachment(Base):
    """Archivos adjuntos a una PQRS"""
    __tablename__ = "file_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    pqrs_id = Column(Integer, ForeignKey("pqrs.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False, comment="Nombre original del archivo")
    file_path = Column(String(500), nullable=False, comment="Ruta donde se guardó")
    file_type = Column(String(50), nullable=False, comment="Tipo MIME del archivo")
    file_size = Column(BigInteger, nullable=False, comment="Tamaño en bytes")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    pqrs = relationship("PQRS", back_populates="files")
    uploader = relationship("User")
    
    def __repr__(self):
        return f"<FileAttachment(id={self.id}, name='{self.file_name}')>"