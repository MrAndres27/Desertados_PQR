"""
Punto de entrada principal de FastAPI
Sistema de Gestión de PQRS
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time

from app.core.config import settings, validate_settings
from app.core.database import check_database_connection

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando aplicación PQRS Backend...")
    
    try:
        validate_settings()
        logger.info("✅ Configuración validada")
    except ValueError as e:
        logger.error(f"❌ Error en configuración: {e}")
        raise
    
    db_connected = await check_database_connection()
    if db_connected:
        logger.info("✅ Conexión a BD establecida")
    else:
        logger.warning("⚠️  No se pudo conectar a la BD")
    
    logger.info(f"🌍 Modo: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug: {settings.DEBUG}")
    
    yield
    
    # Shutdown
    logger.info("👋 Cerrando aplicación...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para gestión de PQRS",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Medir tiempo de respuesta"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logging de requests"""
    logger.info(f"📨 {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"✅ {request.method} {request.url.path} - Status: {response.status_code}")
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador de errores de validación"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Error de validación", "errors": errors}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador general de excepciones"""
    logger.error(f"❌ Error: {str(exc)}", exc_info=True)
    
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Error interno del servidor"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Error interno del servidor",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz"""
    return {
        "message": "Bienvenido al Sistema de Gestión de PQRS",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Docs deshabilitados",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check"""
    db_status = await check_database_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_status else "disconnected",
    }


@app.get("/info", tags=["Info"])
async def info():
    """Información de la API"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )