"""
Routers de la API
Sistema PQRS - Equipo Desertados

Este módulo centraliza todos los routers de la aplicación.
"""
from fastapi import APIRouter

# Importar routers individuales
from app.routers import auth

# Router principal que incluye todos los sub-routers
api_router = APIRouter()

# Incluir routers
api_router.include_router(auth.router, tags=["Autenticación"])

# Lista de routers disponibles para importación
__all__ = ["api_router"]