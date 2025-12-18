from typing import List
import requests
import connexion
import os
"""
controller generated to handled auth operation described at:
https://connexion.readthedocs.io/en/latest/security.html
"""

from swagger_server.models.error import Error

AUTH_SERVER = os.getenv('HOST_SYU', 'http://localhost:8080')

def is_valid_token(token):
    """
    Valida un token.
    En producción, implementa:
    - Validación JWT
    - Consulta a BD de sesiones/usuarios
    - Integración con OAuth/IAM
    """
    try:
        resp = requests.get(f"{AUTH_SERVER}/auth", timeout=2, headers={"Accept": "application/json", "Cookie":f"oversound_auth={token}"})
        return resp.json() if resp.ok else None
    except Exception as e:
        print(f"Couldn't connect to SYU microservice: {e}")
        return None


def check_oversound_auth(api_key, required_scopes):
    """
    Verifica autenticación.
    api_key: valor del token (viene de cookie 'oversound_auth')
    required_scopes: permisos requeridos por la ruta (ej. ['write:tracks'])
    
    Devuelve dict con info de usuario si es válido.
    Devuelve None si es inválido (Connexion rechaza con 401).
    """
    print(f"[DEBUG] check_oversound_auth: Inicio - api_key={api_key[:20] if api_key else None}..., required_scopes={required_scopes}")
    
    if not api_key:
        # No hay token -> rechazar
        print("[DEBUG] check_oversound_auth: ERROR - No hay api_key")
        return None
    
    print(f"[DEBUG] check_oversound_auth: Validando token con AUTH_SERVER={AUTH_SERVER}")
    user_info = is_valid_token(api_key)
    print(f"[DEBUG] check_oversound_auth: user_info obtenido = {user_info}")

    if not user_info:
        # Token inválido -> rechazar
        print("[DEBUG] check_oversound_auth: ERROR - Token inválido")
        return None
    
    # Verificar que el usuario tiene los scopes requeridos
    user_scopes = user_info.get('scopes', [])
    print(f"[DEBUG] check_oversound_auth: user_scopes={user_scopes}, required_scopes={required_scopes}")
    if required_scopes and not any(scope in user_scopes for scope in required_scopes):
        # No tiene permisos suficientes -> rechazar
        print("[DEBUG] check_oversound_auth: ERROR - No tiene permisos suficientes")
        return None
    
    # Token válido y con permisos -> aceptar
    print(f"[DEBUG] check_oversound_auth: Token válido y con permisos - retornando user_info={user_info}")
    return user_info