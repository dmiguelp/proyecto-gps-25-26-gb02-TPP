from typing import List
import requests
import connexion
"""
controller generated to handled auth operation described at:
https://connexion.readthedocs.io/en/latest/security.html
"""

from swagger_server.models.error import Error

AUTH_SERVER = 'http://10.1.1.4:8080'

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