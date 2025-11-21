"""
Router de Autenticación
Sistema PQRS - Equipo Desertados

Endpoints:
- POST /auth/login - Iniciar sesión
- POST /auth/register - Registrar nuevo usuario
- POST /auth/refresh - Renovar access token
- POST /auth/change-password - Cambiar contraseña
- GET /auth/validate-username - Validar disponibilidad de username
- GET /auth/validate-email - Validar disponibilidad de email
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.services.auth_service import AuthService, get_auth_service
from app.models.user import User
from app.schemas.auth import Token, TokenData
from app.schemas.users import UserResponse, UserCreate


# =============================================================================
# SCHEMAS ESPECÍFICOS DE AUTENTICACIÓN
# =============================================================================

class LoginRequest(BaseModel):
    """Request para login"""
    username: str = Field(..., description="Username o email")
    password: str = Field(..., min_length=8, description="Contraseña")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "juan123",
                "password": "MiPassword123!"
            }
        }


class RegisterRequest(BaseModel):
    """Request para registro de usuario"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=3, max_length=200)
    document_type: str = Field(..., description="Tipo de documento: CC, CE, TI, etc.")
    document_number: str = Field(..., min_length=5, max_length=20)
    phone: str | None = None
    address: str | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "juan123",
                "email": "juan@example.com",
                "password": "MiPassword123!",
                "full_name": "Juan Pérez",
                "document_type": "CC",
                "document_number": "1234567890",
                "phone": "3001234567",
                "address": "Calle 123 #45-67"
            }
        }


class ChangePasswordRequest(BaseModel):
    """Request para cambio de contraseña"""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "PasswordActual123!",
                "new_password": "PasswordNuevo456!"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request para refresh token"""
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ValidationResponse(BaseModel):
    """Response para validaciones"""
    available: bool
    message: str


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)


# =============================================================================
# ENDPOINTS PÚBLICOS (Sin autenticación)
# =============================================================================

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Iniciar sesión y obtener tokens JWT
    
    - **username**: Username o email del usuario
    - **password**: Contraseña
    
    Returns:
        - **access_token**: Token JWT para autenticación (expira en 30 min)
        - **refresh_token**: Token para renovar el access token (expira en 7 días)
        - **token_type**: Tipo de token (siempre "bearer")
    """
    auth_service = get_auth_service(db)
    
    tokens = await auth_service.login(
        username=request.username,
        password=request.password
    )
    
    return Token(**tokens)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Registrar un nuevo usuario en el sistema
    
    El usuario se crea con el rol "Usuario" por defecto y estado activo.
    
    Returns:
        Usuario creado sin contraseña
    """
    auth_service = get_auth_service(db)
    
    user = await auth_service.register(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        document_type=request.document_type,
        document_number=request.document_number,
        phone=request.phone,
        address=request.address
    )
    
    return user


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Renovar access token usando un refresh token válido
    
    Cuando el access token expira (después de 30 min), puedes usar el refresh token
    para obtener un nuevo par de tokens sin necesidad de volver a hacer login.
    
    Returns:
        Nuevo par de tokens (access y refresh)
    """
    auth_service = get_auth_service(db)
    
    tokens = await auth_service.refresh_access_token(request.refresh_token)
    
    return Token(**tokens)


@router.get("/validate-username", response_model=ValidationResponse)
async def validate_username(
    username: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Validar si un username está disponible
    
    Útil para validación en tiempo real en formularios de registro.
    
    - **username**: Username a validar
    
    Returns:
        - **available**: True si está disponible, False si ya existe
        - **message**: Mensaje descriptivo
    """
    auth_service = get_auth_service(db)
    
    is_available = await auth_service.validate_username_available(username)
    
    return ValidationResponse(
        available=is_available,
        message="Username disponible" if is_available else "Username ya está en uso"
    )


@router.get("/validate-email", response_model=ValidationResponse)
async def validate_email(
    email: EmailStr,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Validar si un email está disponible
    
    Útil para validación en tiempo real en formularios de registro.
    
    - **email**: Email a validar
    
    Returns:
        - **available**: True si está disponible, False si ya existe
        - **message**: Mensaje descriptivo
    """
    auth_service = get_auth_service(db)
    
    is_available = await auth_service.validate_email_available(email)
    
    return ValidationResponse(
        available=is_available,
        message="Email disponible" if is_available else "Email ya está registrado"
    )


# =============================================================================
# ENDPOINTS PROTEGIDOS (Requieren autenticación)
# =============================================================================

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cambiar contraseña del usuario actual
    
    Requiere autenticación. El usuario debe proporcionar su contraseña actual
    y la nueva contraseña.
    
    Returns:
        Mensaje de confirmación
    """
    auth_service = get_auth_service(db)
    
    success = await auth_service.change_password(
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cambiar la contraseña"
        )
    
    return {
        "message": "Contraseña cambiada exitosamente",
        "success": True
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener información del usuario autenticado
    
    Requiere autenticación. Retorna los datos del usuario actual.
    
    Returns:
        Información completa del usuario actual
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Cerrar sesión
    
    En una implementación con lista negra de tokens, aquí se invalidaría el token.
    Por ahora, simplemente retorna confirmación (el cliente debe eliminar los tokens).
    
    Returns:
        Mensaje de confirmación
    """
    # TODO: Implementar lista negra de tokens si se requiere
    # Por ahora, el logout se maneja del lado del cliente eliminando los tokens
    
    return {
        "message": "Sesión cerrada exitosamente",
        "success": True
    }


# =============================================================================
# NOTAS DE IMPLEMENTACIÓN
# =============================================================================

"""
SEGURIDAD:

1. Los endpoints públicos (/login, /register, /refresh) NO requieren autenticación
2. Los endpoints protegidos requieren Bearer token en el header:
   Authorization: Bearer <access_token>

3. El access token expira en 30 minutos
4. El refresh token expira en 7 días
5. Cuando el access token expira, usar /refresh para obtener uno nuevo

FLUJO DE AUTENTICACIÓN:

1. Usuario hace login → Recibe access_token y refresh_token
2. Cliente almacena ambos tokens (localStorage o cookies HttpOnly)
3. Cliente usa access_token en cada request (header Authorization)
4. Cuando access_token expira → Cliente usa refresh_token en /refresh
5. Cliente recibe nuevos tokens y repite desde paso 2

USO CON ANGULAR/FRONTEND:

// Login
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'juan123', password: 'pass123'})
});
const {access_token, refresh_token} = await response.json();
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// Request autenticado
const response = await fetch('/api/pqrs', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});

// Refresh token
if (response.status === 401) {
  const refreshResponse = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      refresh_token: localStorage.getItem('refresh_token')
    })
  });
  const {access_token, refresh_token} = await refreshResponse.json();
  // Guardar nuevos tokens y reintentar request...
}
"""