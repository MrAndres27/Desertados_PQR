"""
Configuración centralizada de la aplicación.

Este módulo maneja todas las variables de entorno y configuraciones
del sistema usando Pydantic Settings para validación automática.

Autor: Equipo Desertados PQRS
Fecha: 2025
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, EmailStr
import secrets


class Settings(BaseSettings):
    """
    Clase principal de configuración.
    
    Todas las variables de entorno se definen aquí y se validan
    automáticamente al iniciar la aplicación.
    
    Las variables se pueden configurar:
    - En el archivo .env
    - Como variables de entorno del sistema
    - Con valores por defecto definidos aquí
    """
    
    # =========================================================================
    # CONFIGURACIÓN DE LA APLICACIÓN
    # =========================================================================
    
    APP_NAME: str = "PQRS Management System"
    """Nombre de la aplicación"""
    
    APP_VERSION: str = "1.0.0"
    """Versión actual de la aplicación"""
    
    DEBUG: bool = False
    """
    Modo debug (desarrollo vs producción).
    True: Activa logs detallados, Swagger UI, etc.
    False: Modo producción seguro
    """
    
    ENVIRONMENT: str = "production"
    """
    Entorno de ejecución: development, staging, production.
    Afecta el comportamiento de logs y errores.
    """
    
    API_V1_PREFIX: str = "/api/v1"
    """Prefijo para todos los endpoints de la API versión 1"""
    
    # =========================================================================
    # CONFIGURACIÓN DEL SERVIDOR
    # =========================================================================
    
    HOST: str = "0.0.0.0"
    """
    Host donde escucha el servidor.
    0.0.0.0 = todas las interfaces (permite acceso externo)
    127.0.0.1 = solo localhost
    """
    
    PORT: int = 8000
    """Puerto donde escucha el servidor HTTP"""
    
    # =========================================================================
    # CONFIGURACIÓN DE BASE DE DATOS (PostgreSQL)
    # =========================================================================
    
    DATABASE_URL: str
    """
    URL de conexión asíncrona a PostgreSQL.
    Formato: postgresql+asyncpg://usuario:contraseña@host:puerto/basedatos
    Requerido para operaciones asíncronas con FastAPI
    """
    
    DATABASE_URL_SYNC: str
    """
    URL de conexión síncrona a PostgreSQL.
    Formato: postgresql://usuario:contraseña@host:puerto/basedatos
    Usado para scripts, migraciones de Alembic, etc.
    """
    
    DB_HOST: str = "localhost"
    """Host del servidor PostgreSQL"""
    
    DB_PORT: int = 5432
    """Puerto del servidor PostgreSQL (por defecto 5432)"""
    
    DB_NAME: str = "pqrs_db"
    """Nombre de la base de datos"""
    
    DB_USER: str = "pqrs_user"
    """Usuario de PostgreSQL"""
    
    DB_PASSWORD: str = "pqrs_password"
    """Contraseña del usuario de PostgreSQL"""
    
    # =========================================================================
    # CONFIGURACIÓN DE SEGURIDAD
    # =========================================================================
    
    SECRET_KEY: str = secrets.token_urlsafe(32)
    """
    Clave secreta para firmar tokens JWT.
    CRÍTICO: Debe ser única y segura en producción.
    Se genera automáticamente si no se proporciona.
    Mínimo 32 caracteres.
    """
    
    ALGORITHM: str = "HS256"
    """Algoritmo para firmar tokens JWT (HS256 es el estándar)"""
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    """Tiempo de vida de los tokens de acceso (en minutos)"""
    
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    """Tiempo de vida de los tokens de refresco (en días)"""
    
    # =========================================================================
    # POLÍTICA DE CONTRASEÑAS
    # =========================================================================
    
    MIN_PASSWORD_LENGTH: int = 8
    """Longitud mínima de contraseñas"""
    
    REQUIRE_UPPERCASE: bool = True
    """¿Requerir al menos una letra mayúscula?"""
    
    REQUIRE_LOWERCASE: bool = True
    """¿Requerir al menos una letra minúscula?"""
    
    REQUIRE_NUMBERS: bool = True
    """¿Requerir al menos un número?"""
    
    REQUIRE_SPECIAL_CHARS: bool = True
    """¿Requerir al menos un carácter especial?"""
    
    # =========================================================================
    # CONFIGURACIÓN DE CORS (Cross-Origin Resource Sharing)
    # =========================================================================
    
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    """
    Lista de orígenes permitidos para hacer peticiones al backend.
    Importante para permitir que el frontend se comunique con el backend.
    Puede ser una lista separada por comas en el .env
    """
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        """
        Validador que convierte string separado por comas a lista.
        
        Permite configurar CORS_ORIGINS como:
        - Lista: ["http://localhost:3000", "http://localhost:8000"]
        - String: "http://localhost:3000,http://localhost:8000"
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # =========================================================================
    # CONFIGURACIÓN DE EMAIL (SMTP)
    # =========================================================================
    
    MAIL_USERNAME: str
    """Usuario/email para enviar correos (ej: notificaciones@empresa.com)"""
    
    MAIL_PASSWORD: str
    """Contraseña del email (o app password en Gmail)"""
    
    MAIL_FROM: EmailStr
    """Dirección de email que aparecerá como remitente"""
    
    MAIL_FROM_NAME: str = "PQRS System"
    """Nombre que aparecerá como remitente"""
    
    MAIL_PORT: int = 587
    """Puerto SMTP (587 para TLS, 465 para SSL, 25 sin cifrado)"""
    
    MAIL_SERVER: str = "smtp.gmail.com"
    """Servidor SMTP (Gmail, Outlook, etc.)"""
    
    MAIL_TLS: bool = True
    """¿Usar TLS? (recomendado para seguridad)"""
    
    MAIL_SSL: bool = False
    """¿Usar SSL? (alternativa a TLS, no usar ambos)"""
    
    MAIL_USE_CREDENTIALS: bool = True
    """¿Requiere autenticación el servidor SMTP?"""
    
    # =========================================================================
    # CONFIGURACIÓN DE ARCHIVOS
    # =========================================================================
    
    MAX_FILE_SIZE_MB: int = 10
    """Tamaño máximo de archivos a subir (en MB)"""
    
    ALLOWED_FILE_TYPES: str = "pdf,doc,docx,jpg,jpeg,png,txt"
    """Extensiones de archivo permitidas (separadas por comas)"""
    
    UPLOAD_DIR: str = "uploads"
    """Directorio donde se guardan archivos subidos"""
    
    EXPORTS_DIR: str = "exports"
    """Directorio donde se guardan reportes exportados"""
    
    @property
    def max_file_size_bytes(self) -> int:
        """
        Convierte el tamaño máximo de MB a bytes.
        
        Returns:
            int: Tamaño máximo en bytes
        """
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """
        Convierte el string de extensiones a lista.
        
        Returns:
            List[str]: Lista de extensiones permitidas
        """
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",")]
    
    # =========================================================================
    # CONFIGURACIÓN DE PQRS (Plazos de Atención)
    # =========================================================================
    
    PQRS_DEADLINE_PETICION: int = 15
    """Días hábiles para atender una PETICIÓN"""
    
    PQRS_DEADLINE_QUEJA: int = 15
    """Días hábiles para atender una QUEJA"""
    
    PQRS_DEADLINE_RECLAMO: int = 15
    """Días hábiles para atender un RECLAMO"""
    
    PQRS_DEADLINE_SUGERENCIA: int = 30
    """Días hábiles para atender una SUGERENCIA"""
    
    # =========================================================================
    # CONFIGURACIÓN DE SEMAFORIZACIÓN
    # =========================================================================
    
    SEMAPHORE_GREEN_THRESHOLD: int = 60
    """
    Umbral para semáforo verde (% del tiempo transcurrido).
    Si ha pasado menos del 60% del plazo → Verde
    """
    
    SEMAPHORE_YELLOW_THRESHOLD: int = 90
    """
    Umbral para semáforo amarillo (% del tiempo transcurrido).
    Si ha pasado entre 60% y 90% del plazo → Amarillo
    Si ha pasado más del 90% → Rojo
    """
    
    # =========================================================================
    # CONFIGURACIÓN DE REDIS (para caché y Celery)
    # =========================================================================
    
    REDIS_HOST: str = "localhost"
    """Host del servidor Redis"""
    
    REDIS_PORT: int = 6379
    """Puerto de Redis (por defecto 6379)"""
    
    REDIS_DB: int = 0
    """Número de base de datos de Redis (0-15)"""
    
    REDIS_URL: str = "redis://localhost:6379/0"
    """URL completa de conexión a Redis"""
    
    # =========================================================================
    # CONFIGURACIÓN DE CELERY (Tareas en segundo plano)
    # =========================================================================
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    """URL del broker de mensajes para Celery (usando Redis)"""
    
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    """URL donde Celery guarda resultados de tareas"""
    
    # =========================================================================
    # CONFIGURACIÓN DE RATE LIMITING (Límite de peticiones)
    # =========================================================================
    
    RATE_LIMIT_PER_MINUTE: int = 60
    """Máximo de peticiones por minuto por usuario"""
    
    RATE_LIMIT_PER_HOUR: int = 1000
    """Máximo de peticiones por hora por usuario"""
    
    # =========================================================================
    # CONFIGURACIÓN DE LOGGING (Registros)
    # =========================================================================
    
    LOG_LEVEL: str = "INFO"
    """
    Nivel de logs: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    DEBUG: Todo (desarrollo)
    INFO: Información general (recomendado)
    WARNING: Solo advertencias
    ERROR: Solo errores
    """
    
    LOG_FILE: str = "logs/app.log"
    """Archivo donde se guardan los logs"""
    
    LOG_FORMAT: str = "json"
    """Formato de logs: json o text"""
    
    # =========================================================================
    # CONFIGURACIÓN DE RESPALDOS (Backups)
    # =========================================================================
    
    BACKUP_ENABLED: bool = True
    """¿Activar respaldos automáticos?"""
    
    BACKUP_HOUR: int = 2
    """Hora del día para ejecutar respaldo automático (0-23)"""
    
    BACKUP_DIR: str = "backups"
    """Directorio donde se guardan los respaldos"""
    
    BACKUP_RETENTION_DAYS: int = 30
    """Días que se mantienen los respaldos antes de eliminarlos"""
    
    # =========================================================================
    # CONFIGURACIÓN DE PAGINACIÓN
    # =========================================================================
    
    DEFAULT_PAGE_SIZE: int = 20
    """Número de registros por página por defecto"""
    
    MAX_PAGE_SIZE: int = 100
    """Máximo de registros que se pueden pedir en una página"""
    
    # =========================================================================
    # CONFIGURACIÓN REGIONAL
    # =========================================================================
    
    TIMEZONE: str = "America/Bogota"
    """Zona horaria para fechas y horas"""
    
    # =========================================================================
    # CONFIGURACIÓN DE FRONTEND
    # =========================================================================
    
    FRONTEND_URL: str = "http://localhost:3000"
    """URL del frontend (para enlaces en emails, etc.)"""
    
    # =========================================================================
    # MONITOREO Y ANÁLISIS (Opcional)
    # =========================================================================
    
    SENTRY_DSN: Optional[str] = None
    """
    DSN de Sentry para monitoreo de errores (opcional).
    Si se configura, todos los errores se envían a Sentry.
    """
    
    # =========================================================================
    # CONFIGURACIÓN DE PYDANTIC
    # =========================================================================
    
    class Config:
        """Configuración de cómo Pydantic lee las variables"""
        
        env_file = ".env"
        """Leer variables del archivo .env"""
        
        case_sensitive = True
        """Los nombres de variables son sensibles a mayúsculas"""
        
        extra = "ignore"
        """Ignorar variables extra que no estén definidas"""


# =============================================================================
# INSTANCIA GLOBAL DE CONFIGURACIÓN
# =============================================================================

settings = Settings()
"""
Instancia única de configuración para toda la aplicación.
Se puede importar en cualquier módulo con:
    from app.core.config import settings
"""


# =============================================================================
# FUNCIÓN DE VALIDACIÓN
# =============================================================================

def validate_settings():
    """
    Valida que la configuración sea correcta al iniciar la aplicación.
    
    Verifica:
    - Que existan todas las variables requeridas
    - Que SECRET_KEY tenga longitud suficiente
    - Otros requisitos críticos
    
    Returns:
        bool: True si todo está correcto
        
    Raises:
        ValueError: Si falta alguna configuración requerida
    """
    # Variables que DEBEN estar configuradas
    required = ["DATABASE_URL", "SECRET_KEY", "MAIL_USERNAME", "MAIL_PASSWORD"]
    
    # Verificar si falta alguna
    missing = [s for s in required if not getattr(settings, s, None)]
    
    if missing:
        raise ValueError(
            f"❌ Faltan variables de entorno requeridas: {', '.join(missing)}\n"
            f"Por favor, configúralas en el archivo .env"
        )
    
    # Verificar longitud de SECRET_KEY (debe ser fuerte)
    if len(settings.SECRET_KEY) < 32:
        raise ValueError(
            "❌ SECRET_KEY debe tener al menos 32 caracteres para ser segura.\n"
            "Genera una nueva con: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    return True