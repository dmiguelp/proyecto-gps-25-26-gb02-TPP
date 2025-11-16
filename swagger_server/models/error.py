# coding: utf-8
"""
Modelo Error - Representación de errores HTTP estandarizada.

Este módulo define el modelo de datos para las respuestas de error del API.
Proporciona una estructura consistente para comunicar errores al cliente,
incluyendo código de error y mensaje descriptivo.

Características:
    - Formato estandarizado para todos los errores del API
    - Código de error (generalmente coincide con HTTP status code)
    - Mensaje descriptivo legible por humanos
    - Serialización automática a JSON
    - Validación de campos requeridos

Uso típico:
    Los controladores retornan instancias de Error cuando ocurren problemas:
        - (Error(code="404", message="Usuario no encontrado"), 404)
        - (Error(code="500", message="Error de base de datos"), 500)

Schema OpenAPI:
    Definido en swagger.yaml bajo components/schemas/Error

Estándar HTTP:
    El código de error típicamente coincide con el código de estado HTTP,
    aunque puede incluir códigos personalizados para errores de negocio.
"""

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class Error(Model):
    """
    Modelo de respuesta de error estandarizado del API.
    
    Representa un error que ha ocurrido durante el procesamiento de una petición.
    Proporciona información sobre el tipo de error y una descripción útil para
    debugging o mostrar al usuario.
    
    Attributes:
        code (str): Código de error. Generalmente coincide con el código HTTP
                    (400, 401, 404, 500, etc.) pero puede ser personalizado.
                    Requerido.
        message (str): Mensaje descriptivo del error. Debe ser claro y útil
                      para debugging. Puede mostrarse al usuario final.
                      Requerido.
    
    JSON Mapping:
        - code ↔ code
        - message ↔ message
    
    Examples:
        >>> # Error de autenticación
        >>> error = Error(code="401", message="Token inválido o expirado")
        
        >>> # Error de validación
        >>> error = Error(code="400", message="El campo 'email' es requerido")
        
        >>> # Error de servidor
        >>> error = Error(code="500", message="Error interno del servidor")
        
        >>> # Serializar a JSON
        >>> error_dict = error.to_dict()
        >>> # {"code": "500", "message": "Error interno del servidor"}
    
    Validation:
        Ambos campos son obligatorios. Intentar crear una instancia sin
        code o message lanzará ValueError al usar los setters.
    
    Note:
        Este modelo es generado automáticamente por Swagger Codegen.
        Modificaciones manuales pueden perderse al regenerar.
    """
    def __init__(self, code: str=None, message: str=None):  # noqa: E501
        """
        Constructor del modelo Error.
        
        Inicializa una instancia de Error con código y mensaje.
        Configura los tipos de datos y el mapeo entre atributos Python y JSON.
        
        Args:
            code (str): Código de error. Típicamente un código HTTP como "400", "500".
            message (str): Mensaje descriptivo del error para debugging o usuario.
        
        Note:
            Ambos parámetros son técnicamente opcionales en el constructor,
            pero se vuelven obligatorios al usar los setters (lanzan ValueError si son None).
        """
        self.swagger_types = {
            'code': str,
            'message': str
        }

        self.attribute_map = {
            'code': 'code',
            'message': 'message'
        }
        self._code = code
        self._message = message

    @classmethod
    def from_dict(cls, dikt) -> 'Error':
        """
        Crea una instancia de Error desde un diccionario.
        
        Deserializa un diccionario en un objeto Error, útil para procesar
        errores recibidos de otros servicios o para testing.
        
        Args:
            dikt (dict): Diccionario con los datos del error.
                        Debe contener: code y message.
        
        Returns:
            Error: Nueva instancia con los datos deserializados.
        
        Example:
            >>> error_data = {"code": "404", "message": "Not found"}
            >>> error = Error.from_dict(error_data)
        """
        return util.deserialize_model(dikt, cls)

    @property
    def code(self) -> str:
        """Gets the code of this Error.


        :return: The code of this Error.
        :rtype: str
        """
        return self._code

    @code.setter
    def code(self, code: str):
        """Sets the code of this Error.


        :param code: The code of this Error.
        :type code: str
        """
        if code is None:
            raise ValueError("Invalid value for `code`, must not be `None`")  # noqa: E501

        self._code = code

    @property
    def message(self) -> str:
        """Gets the message of this Error.


        :return: The message of this Error.
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message: str):
        """Sets the message of this Error.


        :param message: The message of this Error.
        :type message: str
        """
        if message is None:
            raise ValueError("Invalid value for `message`, must not be `None`")  # noqa: E501

        self._message = message
