from typing import List
import requests
import connexion
import os
from swagger_server.models.error import Error
"""
Controlador de autorización y autenticación.
"""

AUTH_SERVER = '10.1.1.4:8080'

def is_valid_token(token):
    """
    Delega validación del token al servidor de autenticación.
    
    En modo TEST (variable TESTING=true), retorna un usuario mockeado
    para evitar dependencias externas.
    """
    # Si estamos en modo test, retornar usuario mockeado
    if os.environ.get('TESTING') == 'true':
        return {
            'id': 1,
            'username': 'test_user',
            'scopes': ['read:cart', 'write:cart', 'read:payment', 'write:payment', 
                       'read:purchase', 'write:purchase', 'read:store', 'write:store']
        }
    
    resp = requests.get(f"{AUTH_SERVER}/auth", timeout=2, headers={"Accept": "application/json", "Cookie":f"oversound_auth={token}"})
    
    return resp.json() if resp.ok else None

def check_oversounds_auth(api_key, required_scopes):
    """
    Verifica autenticación para el microservicio OverSounds.
    api_key: valor del token (viene de cookie 'token')
    required_scopes: permisos requeridos por la ruta (ej. ['write:purchases'])
    
    Devuelve dict con info de usuario si es válido.
    Devuelve None si es inválido (Connexion rechaza con 401).
    """
    if not api_key:
        # No hay token -> rechazar
        return None
    
    user_info = is_valid_token(api_key)

    if not user_info:
        # Token inválido -> rechazar
        return None
    
    # Verificar que el usuario tiene los scopes requeridos
    user_scopes = user_info.get('scopes', [])
    if required_scopes and not any(scope in user_scopes for scope in required_scopes):
        # No tiene permisos suficientes -> rechazar
        return None
    
    # Token válido y con permisos -> aceptar
    return user_info


def check_bandcamp_auth(api_key, required_scopes):
    """
    Verifica autenticación.
    api_key: valor del token (viene de cookie 'token')
    required_scopes: permisos requeridos por la ruta (ej. ['write:tracks'])
    
    Devuelve dict con info de usuario si es válido.
    Devuelve None si es inválido (Connexion rechaza con 401).
    """
    if not api_key:
        # No hay token -> rechazar
        return None
    
    user_info = is_valid_token(api_key)

    if not user_info:
        # Token inválido -> rechazar
        return None
    
    # Verificar que el usuario tiene los scopes requeridos
    user_scopes = user_info.get('scopes', [])
    if required_scopes and not any(scope in user_scopes for scope in required_scopes):
        # No tiene permisos suficientes -> rechazar
        return None
    
    # Token válido y con permisos -> aceptar
    return user_info


def verify_token_and_get_user_id():
    """
    Verifica el token de la cookie actual y extrae el ID de usuario.
    
    Obtiene automáticamente el token de la cookie 'token' de la request actual
    y verifica su validez con el servidor de autenticación.
    
    Returns:
        tuple: (user_id, error_response) 
               Si es válido: (user_id, None)
               Si es inválido: (None, (Error, status_code))
    
    Examples:
        En un controller:
            >>> user_id, error = verify_token_and_get_user_id()
            >>> if error:
            ...     return error
            >>> # Continuar con user_id válido
    
    Note:
        - Obtiene el token automáticamente de connexion.request.cookies
        - Retorna tupla (user_id, error) para manejo explícito de errores
        - Los controladores DEBEN verificar si hay error antes de continuar
        - Si hay error, el controller debe retornar inmediatamente
    """
    # Obtener token de la cookie
    token = connexion.request.cookies.get('token')
    
    if not token:
        error = Error(code="401", message="Token de usuario no encontrado.")
        return None, (error, 401)
    
    try:
        user_info = is_valid_token(token)
        
        if not user_info:
            error = Error(code="403", message="Usuario no autorizado o token inválido.")
            return None, (error, 403)
        
        user_id = user_info.get("id")
        
        if not user_id:
            error = Error(code="404", message="Usuario no encontrado.")
            return None, (error, 404)
        
        return user_id, None
        
    except requests.exceptions.RequestException as e:
        error = Error(code="503", message=f"No se pudo contactar con el microservicio de autenticación: {e}")
        return None, (error, 503)
    except Exception as e:
        error = Error(code="500", message=f"Error inesperado al verificar token: {e}")
        return None, (error, 500)