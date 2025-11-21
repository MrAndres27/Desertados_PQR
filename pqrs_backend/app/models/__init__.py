"""
Módulo de modelos de base de datos.
Importa todos los modelos para que Alembic los detecte.
"""

from app.core.database import Base
from app.models.user import User
from app.models.role import Role, role_permissions
from app.models.permission import Permission
from app.models.pqrs_status import PQRSStatus
from app.models.pqrs import PQRS, PQRSType, PQRSPriority, SemaphoreColor
from app.models.pqrs_history import PQRSHistory
from app.models.file_attachment import FileAttachment
from app.models.notification import Notification, NotificationType
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "role_permissions",
    "PQRSStatus",
    "PQRS",
    "PQRSType",
    "PQRSPriority",
    "SemaphoreColor",
    "PQRSHistory",
    "FileAttachment",
    "Notification",
    "NotificationType",
    "AuditLog",
]
