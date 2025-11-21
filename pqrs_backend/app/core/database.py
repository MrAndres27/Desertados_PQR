"""
Configuración de base de datos con SQLAlchemy.

Maneja todas las conexiones y sesiones de base de datos.
Soporta operaciones tanto síncronas como asíncronas.

Autor: Equipo Desertados PQRS
Fecha: 2025
"""

from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


# =============================================================================
# BASE DECLARATIVA
# =============================================================================

Base = declarative_base()
"""
Clase base para todos los modelos de SQLAlchemy.

Todos los modelos de base de datos deben heredar de esta clase.

Ejemplo:
    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        ...
"""


# =============================================================================
# CONFIGURACIÓN SÍNCRONA (Para scripts, migraciones Alembic, etc.)
# =============================================================================

# Motor de base de datos síncrono
engine = create_engine(
    settings.DATABASE_URL_SYNC,  # URL de conexión síncrona
    pool_pre_ping=True,  # Verifica que la conexión esté viva antes de usarla
    pool_size=10,  # Número de conexiones en el pool permanentemente
    max_overflow=20,  # Conexiones adicionales si el pool está lleno
    echo=settings.DEBUG,  # Imprime SQL en consola si DEBUG=True
)
"""
Motor síncrono de SQLAlchemy.

Configuración del connection pool:
- pool_size=10: Mantiene 10 conexiones abiertas permanentemente
- max_overflow=20: Puede crear hasta 20 conexiones adicionales temporales
- Total máximo: 30 conexiones simultáneas

pool_pre_ping=True: Evita errores "connection closed" verificando
antes de usar cada conexión (pequeño overhead pero más confiable)
"""

# Session factory síncrono
SessionLocal = sessionmaker(
    autocommit=False,  # No hacer commit automático (control manual)
    autoflush=False,  # No hacer flush automático antes de queries
    bind=engine  # Enlazar con el motor creado arriba
)
"""
Factory para crear sesiones síncronas.

autocommit=False: Debemos hacer commit() manualmente para guardar cambios.
autoflush=False: Debemos hacer flush() manualmente para sincronizar con BD.

Esto da mayor control sobre las transacciones.
"""


def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesiones síncronas de base de datos.
    
    Crea una sesión, la entrega para usar, y la cierra automáticamente.
    Para usar como dependencia en FastAPI.
    
    Yields:
        Session: Sesión de SQLAlchemy lista para usar
        
    Ejemplo con FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
            
    Nota:
        La sesión se cierra automáticamente al terminar la función,
        incluso si hay un error.
    """
    # Crear nueva sesión
    db = SessionLocal()
    
    try:
        # Entregar la sesión al código que la necesita
        yield db
    finally:
        # Cerrar la sesión pase lo que pase
        db.close()


# =============================================================================
# CONFIGURACIÓN ASÍNCRONA (Para operaciones asíncronas con FastAPI)
# =============================================================================

# Motor de base de datos asíncrono
async_engine = create_async_engine(
    settings.DATABASE_URL,  # URL de conexión asíncrona (asyncpg)
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)
"""
Motor asíncrono de SQLAlchemy.

Usa asyncpg para conexiones asíncronas a PostgreSQL.
Configuración similar al motor síncrono pero optimizado para async/await.
"""

# Session factory asíncrono
AsyncSessionLocal = async_sessionmaker(
    async_engine,  # Motor asíncrono
    class_=AsyncSession,  # Tipo de sesión
    expire_on_commit=False,  # No expirar objetos después de commit
    autocommit=False,
    autoflush=False,
)
"""
Factory para crear sesiones asíncronas.

expire_on_commit=False: Los objetos no se marcan como "expirados" después
de hacer commit. Esto permite acceder a sus atributos sin hacer otra query.
"""


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesiones asíncronas de base de datos.
    
    Crea una sesión asíncrona, la entrega, hace commit si todo va bien,
    o rollback si hay error, y la cierra automáticamente.
    
    Yields:
        AsyncSession: Sesión asíncrona de SQLAlchemy
        
    Ejemplo con FastAPI:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(User))
            users = result.scalars().all()
            return users
            
    Nota:
        - Se hace commit() automático si no hay errores
        - Se hace rollback() automático si hay alguna excepción
        - La sesión se cierra siempre al final
    """
    # Crear nueva sesión asíncrona
    async with AsyncSessionLocal() as session:
        try:
            # Entregar la sesión
            yield session
            
            # Si todo va bien, hacer commit
            await session.commit()
            
        except Exception:
            # Si hay error, hacer rollback (deshacer cambios)
            await session.rollback()
            
            # Re-lanzar la excepción para que FastAPI la maneje
            raise
            
        finally:
            # Cerrar la sesión
            await session.close()


# =============================================================================
# FUNCIONES DE INICIALIZACIÓN
# =============================================================================

async def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.
    
    Lee todos los modelos que heredan de Base y crea sus tablas
    en la base de datos si no existen.
    
    ⚠️ IMPORTANTE: Solo para desarrollo/testing.
    En producción usa Alembic para migraciones.
    
    Ejemplo:
        async def startup():
            await init_db()
            print("Base de datos inicializada")
    """
    # Crear conexión asíncrona
    async with async_engine.begin() as conn:
        # Ejecutar create_all() de forma asíncrona
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    PELIGROSO: Elimina todas las tablas de la base de datos.
    
    ⚠️ ADVERTENCIA: Esto borra TODOS los datos.
    Solo usar en testing y desarrollo.
    
    Ejemplo:
        async def reset_database():
            await drop_db()
            await init_db()
            print("Base de datos reiniciada")
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def init_db_sync() -> None:
    """
    Inicializa la base de datos de forma síncrona.
    
    Versión síncrona de init_db(). Útil para scripts.
    
    Ejemplo:
        if __name__ == "__main__":
            init_db_sync()
            print("BD inicializada")
    """
    Base.metadata.create_all(bind=engine)


def drop_db_sync() -> None:
    """
    PELIGROSO: Elimina todas las tablas (versión síncrona).
    
    ⚠️ ADVERTENCIA: Esto borra TODOS los datos.
    """
    Base.metadata.drop_all(bind=engine)


# =============================================================================
# HEALTH CHECKS (Verificación de Conexión)
# =============================================================================

async def check_database_connection() -> bool:
    """
    Verifica que la conexión a la base de datos esté activa.
    
    Intenta ejecutar un SELECT 1 simple para comprobar conectividad.
    
    Returns:
        bool: True si la conexión es exitosa, False si hay error
        
    Ejemplo:
        @app.get("/health")
        async def health():
            db_ok = await check_database_connection()
            return {
                "status": "healthy" if db_ok else "unhealthy",
                "database": "connected" if db_ok else "disconnected"
            }
    """
    try:
        # Intentar hacer una query simple
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        
        return True
        
    except Exception as e:
        # Si hay error, imprimir para debugging
        print(f"❌ Error de conexión a base de datos: {e}")
        return False


def check_database_connection_sync() -> bool:
    """
    Verifica la conexión a BD de forma síncrona.
    
    Versión síncrona de check_database_connection().
    Útil para scripts o verificaciones antes de iniciar la app.
    
    Returns:
        bool: True si hay conexión, False si no
        
    Ejemplo:
        if __name__ == "__main__":
            if check_database_connection_sync():
                print("✅ Conexión a BD OK")
            else:
                print("❌ No hay conexión a BD")
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Error de conexión a BD: {e}")
        return False


# =============================================================================
# CONTEXTOS DE TRANSACCIÓN (Control Manual Avanzado)
# =============================================================================

class DatabaseContext:
    """
    Contexto para manejar transacciones síncronas de forma explícita.
    
    Permite control manual completo de commits y rollbacks.
    Útil para operaciones complejas que requieren control fino.
    
    Ejemplo:
        with DatabaseContext() as db:
            # Hacer varias operaciones
            user = User(name="Juan")
            db.add(user)
            
            order = Order(user_id=user.id)
            db.add(order)
            
            # Si algo sale mal aquí, se hace rollback automático
            # Si todo sale bien, se hace commit automático
    """
    
    def __init__(self):
        """Inicializa el contexto sin crear la sesión aún."""
        self.db: Session = None
    
    def __enter__(self) -> Session:
        """
        Entra al contexto y crea la sesión.
        
        Returns:
            Session: Sesión de base de datos lista para usar
        """
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Sale del contexto y cierra la sesión.
        
        Args:
            exc_type: Tipo de excepción si la hubo
            exc_val: Valor de la excepción
            exc_tb: Traceback de la excepción
            
        Si hay excepción: hace rollback
        Si no hay excepción: hace commit
        Siempre: cierra la sesión
        """
        if exc_type is not None:
            # Hubo error, deshacer cambios
            self.db.rollback()
        else:
            # Todo bien, guardar cambios
            self.db.commit()
        
        # Cerrar sesión
        self.db.close()


class AsyncDatabaseContext:
    """
    Contexto para manejar transacciones asíncronas.
    
    Versión asíncrona de DatabaseContext.
    
    Ejemplo:
        async with AsyncDatabaseContext() as db:
            user = User(name="Juan")
            db.add(user)
            await db.flush()
            
            # Operaciones asíncronas...
    """
    
    def __init__(self):
        """Inicializa el contexto."""
        self.db: AsyncSession = None
    
    async def __aenter__(self) -> AsyncSession:
        """
        Entra al contexto asíncrono.
        
        Returns:
            AsyncSession: Sesión asíncrona lista para usar
        """
        self.db = AsyncSessionLocal()
        return self.db
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Sale del contexto asíncrono.
        
        Maneja commit/rollback automáticamente según si hubo error.
        """
        if exc_type is not None:
            # Hubo error
            await self.db.rollback()
        else:
            # Todo bien
            await self.db.commit()
        
        # Cerrar
        await self.db.close()


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def get_db_url() -> str:
    """
    Obtiene la URL de conexión síncrona actual.
    
    Útil para debugging o logging.
    
    Returns:
        str: URL de conexión (sin contraseña expuesta)
    """
    url = str(engine.url)
    # Ocultar contraseña para seguridad
    if '@' in url and ':' in url:
        parts = url.split('@')
        user_pass = parts[0].split(':')
        if len(user_pass) > 1:
            url = f"{user_pass[0]}:****@{parts[1]}"
    return url


async def get_async_db_url() -> str:
    """
    Obtiene la URL de conexión asíncrona actual.
    
    Returns:
        str: URL de conexión (sin contraseña expuesta)
    """
    url = str(async_engine.url)
    # Ocultar contraseña
    if '@' in url and ':' in url:
        parts = url.split('@')
        user_pass = parts[0].split(':')
        if len(user_pass) > 1:
            url = f"{user_pass[0]}:****@{parts[1]}"
    return url