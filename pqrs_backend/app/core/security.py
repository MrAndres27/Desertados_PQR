"""
Módulo de seguridad del sistema.

Maneja toda la seguridad de la aplicación incluyendo:
- Hashing de contraseñas con bcrypt
- Creación y verificación de tokens JWT
- Validación de políticas de contraseñas
- Funciones de autorización

Autor: Equipo Desertados PQRS
Fecha: 2025
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# =============================================================================
# CONTEXTO DE HASHING DE CONTRASEÑAS
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
"""
Contexto de PassLib para hash de contraseñas.
Usa bcrypt, que es el estándar de la industria para hashear contraseñas.
"""


# =============================================================================
# FUNCIONES DE CONTRASEÑAS
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash.
    
    Usa bcrypt para verificar de forma segura sin exponer la contraseña real.
    
    Args:
        plain_password: Contraseña en texto plano (la que ingresa el usuario)
        hashed_password: Hash de la contraseña guardado en la base de datos
        
    Returns:
        bool: True si la contraseña es correcta, False si no
        
    Ejemplo:
        >>> hash_guardado = "$2b$12$..."  # Hash de la BD
        >>> password_ingresada = "MiContraseña123!"
        >>> if verify_password(password_ingresada, hash_guardado):
        ...     print("¡Contraseña correcta!")
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    
    Convierte una contraseña en texto plano a un hash seguro
    que se puede guardar en la base de datos.
    
    IMPORTANTE: Nunca guardes contraseñas en texto plano.
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        str: Hash de la contraseña (seguro para guardar en BD)
        
    Ejemplo:
        >>> password = "MiContraseña123!"
        >>> hash = get_password_hash(password)
        >>> print(hash)  # $2b$12$... (siempre diferente cada vez)
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Valida que una contraseña cumpla con las políticas de seguridad.
    
    Verifica según las configuraciones en settings:
    - Longitud mínima
    - Requiere mayúsculas
    - Requiere minúsculas
    - Requiere números
    - Requiere caracteres especiales
    
    Args:
        password: Contraseña a validar
        
    Returns:
        tuple[bool, list[str]]: 
            - bool: True si es válida, False si no
            - list[str]: Lista de errores encontrados (vacía si es válida)
            
    Ejemplo:
        >>> es_valida, errores = validate_password_strength("abc")
        >>> print(es_valida)  # False
        >>> print(errores)  # ["Mínimo 8 caracteres", "Debe contener mayúsculas", ...]
    """
    errors = []
    
    # Verificar longitud mínima
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        errors.append(f"Mínimo {settings.MIN_PASSWORD_LENGTH} caracteres")
    
    # Verificar mayúsculas (A-Z)
    if settings.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        errors.append("Debe contener al menos una letra mayúscula")
    
    # Verificar minúsculas (a-z)
    if settings.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        errors.append("Debe contener al menos una letra minúscula")
    
    # Verificar números (0-9)
    if settings.REQUIRE_NUMBERS and not re.search(r"\d", password):
        errors.append("Debe contener al menos un número")
    
    # Verificar caracteres especiales (!@#$%^&* etc.)
    if settings.REQUIRE_SPECIAL_CHARS and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Debe contener al menos un carácter especial (!@#$%^&*...)")
    
    # Si no hay errores, la contraseña es válida
    return len(errors) == 0, errors


# =============================================================================
# FUNCIONES DE TOKENS JWT
# =============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT de acceso.
    
    Los tokens de acceso son de corta duración (30 minutos por defecto)
    y se usan para autenticar cada petición a la API.
    
    Args:
        data: Datos a incluir en el token (típicamente {"sub": user_id})
        expires_delta: Tiempo de expiración personalizado (opcional)
        
    Returns:
        str: Token JWT codificado
        
    Ejemplo:
        >>> token = create_access_token(data={"sub": 123, "role": "admin"})
        >>> print(token)  # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        
    Nota:
        El token incluye automáticamente:
        - exp: Fecha de expiración
        - iat: Fecha de creación
        - type: "access" (para diferenciar de refresh tokens)
    """
    # Copiar datos para no modificar el original
    to_encode = data.copy()
    
    # Calcular fecha de expiración
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Agregar metadata al token
    to_encode.update({
        "exp": expire,           # Cuándo expira
        "iat": datetime.utcnow(),  # Cuándo se creó
        "type": "access"         # Tipo de token
    })
    
    # Codificar y firmar con la SECRET_KEY
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Crea un token JWT de refresco.
    
    Los tokens de refresco son de larga duración (7 días por defecto)
    y se usan para obtener nuevos tokens de acceso sin volver a hacer login.
    
    Args:
        data: Datos a incluir en el token (típicamente {"sub": user_id})
        
    Returns:
        str: Token JWT de refresco codificado
        
    Ejemplo:
        >>> token = create_refresh_token(data={"sub": 123})
        >>> # Guardar en httpOnly cookie o almacenamiento seguro
        
    Nota:
        El token incluye automáticamente:
        - exp: Fecha de expiración (7 días por defecto)
        - iat: Fecha de creación
        - type: "refresh" (para diferenciar de access tokens)
    """
    # Copiar datos
    to_encode = data.copy()
    
    # Calcular expiración (más largo que access token)
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    # Agregar metadata
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"  # IMPORTANTE: marca como refresh
    })
    
    # Codificar
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica un token JWT sin verificar su tipo.
    
    Útil para inspeccionar el contenido de un token.
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        dict: Payload del token si es válido
        None: Si el token es inválido o ha expirado
        
    Ejemplo:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = decode_token(token)
        >>> print(payload)  # {"sub": 123, "exp": 1234567890, ...}
    """
    try:
        # Decodificar y verificar firma
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        # Token inválido, firma incorrecta, o expirado
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verifica un token JWT y su tipo.
    
    Comprueba que:
    - El token sea válido
    - La firma sea correcta
    - No haya expirado
    - Sea del tipo correcto (access o refresh)
    
    Args:
        token: Token JWT a verificar
        token_type: Tipo esperado ("access" o "refresh")
        
    Returns:
        dict: Payload del token si es válido
        None: Si el token es inválido, expirado o del tipo incorrecto
        
    Ejemplo:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = verify_token(token, token_type="access")
        >>> if payload:
        ...     user_id = payload.get("sub")
        ...     print(f"Usuario autenticado: {user_id}")
        ... else:
        ...     print("Token inválido")
    """
    # Primero decodificar
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    # Verificar que sea del tipo correcto
    if payload.get("type") != token_type:
        return None
    
    # Verificar que no haya expirado (doble check)
    exp = payload.get("exp")
    if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
        return None
    
    return payload


# =============================================================================
# FUNCIONES DE VALIDACIÓN Y SANITIZACIÓN
# =============================================================================

def validate_email(email: str) -> bool:
    """
    Valida el formato de un email.
    
    Verifica que el email tenga un formato válido usando expresión regular.
    
    Args:
        email: Email a validar
        
    Returns:
        bool: True si el formato es válido, False si no
        
    Ejemplo:
        >>> validate_email("usuario@ejemplo.com")  # True
        >>> validate_email("invalido")  # False
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_input(text: str) -> str:
    """
    Sanitiza entrada de usuario para prevenir XSS.
    
    Elimina caracteres peligrosos que podrían usarse en ataques XSS.
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        str: Texto sanitizado
        
    Ejemplo:
        >>> sanitize_input("<script>alert('XSS')</script>")
        >>> # 'scriptalert(XSS)/script'  (sin <>)
        
    Nota:
        Para sanitización más robusta, considera usar bibliotecas
        especializadas como bleach o html.escape
    """
    # Caracteres peligrosos para XSS
    dangerous_chars = ['<', '>', '"', "'", '&', '/', '\\']
    
    sanitized = text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Eliminar espacios extra al inicio/final
    return sanitized.strip()


def generate_password_reset_token(email: str) -> str:
    """
    Genera un token para reseteo de contraseña.
    
    Crea un token especial de corta duración (24 horas) que permite
    al usuario resetear su contraseña.
    
    Args:
        email: Email del usuario que solicita el reset
        
    Returns:
        str: Token JWT para reseteo de contraseña
        
    Ejemplo:
        >>> token = generate_password_reset_token("usuario@ejemplo.com")
        >>> # Enviar por email al usuario
        >>> # El token expira en 24 horas
    """
    # Token válido por 24 horas
    delta = timedelta(hours=24)
    
    # Datos del token
    data = {
        "sub": email,
        "type": "password_reset"
    }
    
    return create_access_token(data, expires_delta=delta)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verifica un token de reseteo de contraseña.
    
    Args:
        token: Token de reseteo a verificar
        
    Returns:
        str: Email del usuario si el token es válido
        None: Si el token es inválido o ha expirado
        
    Ejemplo:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> email = verify_password_reset_token(token)
        >>> if email:
        ...     # Permitir que el usuario cambie su contraseña
        ...     print(f"Reset válido para: {email}")
        ... else:
        ...     print("Token inválido o expirado")
    """
    # Decodificar token
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    # Verificar que sea del tipo correcto
    if payload.get("type") != "password_reset":
        return None
    
    # Retornar el email
    return payload.get("sub")


# =============================================================================
# FUNCIONES DE PERMISOS (Para Control de Acceso)
# =============================================================================

def check_permission(user_permissions: list[str], required_permission: str) -> bool:
    """
    Verifica si un usuario tiene un permiso específico.
    
    Args:
        user_permissions: Lista de permisos del usuario
        required_permission: Permiso requerido
        
    Returns:
        bool: True si tiene el permiso, False si no
        
    Ejemplo:
        >>> permisos_usuario = ["crear_pqrs", "ver_pqrs", "editar_pqrs"]
        >>> if check_permission(permisos_usuario, "editar_pqrs"):
        ...     print("Usuario puede editar PQRS")
    """
    return required_permission in user_permissions


def check_any_permission(
    user_permissions: list[str],
    required_permissions: list[str]
) -> bool:
    """
    Verifica si un usuario tiene AL MENOS UNO de los permisos requeridos.
    
    Útil para casos donde varias acciones alternativas son válidas.
    
    Args:
        user_permissions: Lista de permisos del usuario
        required_permissions: Lista de permisos requeridos (OR lógico)
        
    Returns:
        bool: True si tiene al menos uno, False si no tiene ninguno
        
    Ejemplo:
        >>> permisos_usuario = ["ver_dashboard"]
        >>> requeridos = ["admin", "ver_dashboard", "gestor"]
        >>> if check_any_permission(permisos_usuario, requeridos):
        ...     print("Usuario puede ver el dashboard")
    """
    return any(perm in user_permissions for perm in required_permissions)


def check_all_permissions(
    user_permissions: list[str],
    required_permissions: list[str]
) -> bool:
    """
    Verifica si un usuario tiene TODOS los permisos requeridos.
    
    Útil para acciones que requieren múltiples permisos simultáneamente.
    
    Args:
        user_permissions: Lista de permisos del usuario
        required_permissions: Lista de permisos requeridos (AND lógico)
        
    Returns:
        bool: True si tiene todos, False si falta alguno
        
    Ejemplo:
        >>> permisos_usuario = ["crear_usuario", "editar_usuario", "eliminar_usuario"]
        >>> requeridos = ["crear_usuario", "editar_usuario"]
        >>> if check_all_permissions(permisos_usuario, requeridos):
        ...     print("Usuario tiene todos los permisos necesarios")
    """
    return all(perm in user_permissions for perm in required_permissions)