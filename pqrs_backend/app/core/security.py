"""
Módulo de seguridad - JWT, Hashing y Autenticación
Sistema PQRS - Equipo Desertados

Proporciona funciones para:
- Generación y verificación de tokens JWT
- Hashing y verificación de contraseñas con bcrypt
- Gestión de tokens de acceso y refresh
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# =============================================================================
# CONFIGURACIÓN DE HASHING
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# FUNCIONES DE HASHING DE CONTRASEÑAS
# =============================================================================

def hash_password(password: str) -> str:
    """Genera un hash seguro de una contraseña usando bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash"""
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# FUNCIONES DE TOKENS JWT
# =============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un token JWT de acceso"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un token JWT de refresh"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(
    token: str,
    token_type: str = "access"
) -> Optional[Dict[str, Any]]:
    """
    Verifica y decodifica un token JWT
    
    Returns:
        Dict con el payload si el token es válido, None si es inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != token_type:
            return None
        
        return payload
        
    except JWTError:
        return None


def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
    """Crea un par de tokens (access y refresh) para un usuario"""
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(
        data={"sub": user_data.get("sub")}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Valida que una contraseña cumpla con los requisitos de seguridad
    
    Returns:
        (es_válida, mensaje_de_error)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not any(c.islower() for c in password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un número"
    
    special_chars = "!@#$%^&*(),.?\":{}|<>"
    if not any(c in special_chars for c in password):
        return False, f"La contraseña debe contener al menos un carácter especial"
    
    return True, None