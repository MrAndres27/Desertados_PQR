"""
Routers de la API
Sistema PQRS - Equipo Desertados

Este módulo centraliza todos los routers de la aplicación.
"""
from fastapi import APIRouter

# Importar routers individuales
from app.routers import auth, pqrs, users

# Router principal que incluye todos los sub-routers
api_router = APIRouter()

# Incluir routers
api_router.include_router(auth.router, tags=["Autenticación"])
api_router.include_router(pqrs.router, tags=["PQRS"])
api_router.include_router(users.router, tags=["Usuarios (Admin)"])

# Lista de routers disponibles para importación
__all__ = ["api_router"]