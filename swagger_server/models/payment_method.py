# coding: utf-8
"""
Modelo PaymentMethod - Representación de métodos de pago de usuarios.

Este módulo define el modelo de datos para métodos de pago (tarjetas de crédito/débito)
asociados a usuarios del sistema OverSounds. Almacena información enmascarada de tarjetas
para cumplir con estándares de seguridad como PCI-DSS.

Características:
    - Almacenamiento de información de tarjetas enmascaradas
    - Validación de fechas de vencimiento
    - Serialización/deserialización JSON automática
    - Cumplimiento con estándares de seguridad (datos enmascarados)

Seguridad:
    - Los números de tarjeta se almacenan ENMASCARADOS (ej: "**** **** **** 1234")
    - Nunca se almacenan números completos de tarjetas
    - No se almacena CVV ni información sensible
    - La validación de tarjetas se realiza en servicios externos de pago

Uso típico:
    - Alta de nuevos métodos de pago por usuarios
    - Selección de método de pago durante el proceso de compra
    - Consulta de métodos de pago disponibles del usuario

Schema OpenAPI:
    Definido en swagger.yaml bajo components/schemas/PaymentMethod

Compliance:
    Este modelo está diseñado considerando requisitos PCI-DSS:
        - No almacena datos sensibles completos
        - Números de tarjeta enmascarados
        - Información mínima necesaria para identificación
"""

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class PaymentMethod(Model):
    """
    Modelo de método de pago (tarjeta de crédito/débito).
    
    Representa la información de una tarjeta de pago asociada a un usuario.
    La información se almacena de forma enmascarada para cumplir con requisitos
    de seguridad PCI-DSS.
    
    Attributes:
        card_number (str): Número de tarjeta enmascarado. 
                          Formato típico: "**** **** **** 1234"
                          Solo muestra últimos 4 dígitos. Requerido.
        expire_month (int): Mes de vencimiento de la tarjeta (1-12). Requerido.
        expire_year (int): Año de vencimiento (ej: 2025, 2030). Requerido.
        card_holder (str): Nombre del titular como aparece en la tarjeta. Requerido.
    
    JSON Mapping:
        - card_number ↔ cardNumber
        - expire_month ↔ expireMonth
        - expire_year ↔ expireYear
        - card_holder ↔ cardHolder
    
    Validation:
        - Todos los campos son obligatorios
        - expire_month debe estar entre 1 y 12 (validado en API spec)
        - card_number debe estar enmascarado antes de llegar al backend
    
    Examples:
        >>> # Crear método de pago
        >>> payment = PaymentMethod(
        ...     card_number="**** **** **** 1234",
        ...     expire_month=12,
        ...     expire_year=2025,
        ...     card_holder="Juan Pérez"
        ... )
        
        >>> # Deserializar desde JSON
        >>> data = {
        ...     "cardNumber": "**** **** **** 5678",
        ...     "expireMonth": 6,
        ...     "expireYear": 2026,
        ...     "cardHolder": "María García"
        ... }
        >>> payment = PaymentMethod.from_dict(data)
    
    Security Considerations:
        - NUNCA almacenar números de tarjeta completos
        - NUNCA almacenar CVV/CVC
        - El enmascaramiento debe hacerse en el cliente antes de enviar
        - Para procesar pagos, usar gateway de pago externo con tokenización
    
    Note:
        Este modelo es generado automáticamente por Swagger Codegen.
        La información de seguridad es crítica - revisar antes de modificar.
    """
    def __init__(self, card_number: str=None, expire_month: int=None, expire_year: int=None, card_holder: str=None):  # noqa: E501
        """
        Constructor del modelo PaymentMethod.
        
        Inicializa una instancia de PaymentMethod con la información de la tarjeta.
        Configura los tipos de datos y el mapeo entre atributos Python y JSON.
        
        Args:
            card_number (str): Número de tarjeta ENMASCARADO (ej: "**** **** **** 1234").
            expire_month (int): Mes de vencimiento (1-12).
            expire_year (int): Año de vencimiento (ej: 2025).
            card_holder (str): Nombre del titular de la tarjeta.
        
        Security:
            El card_number DEBE venir ya enmascarado. No aceptar números completos.
        
        Note:
            Todos los parámetros son técnicamente opcionales en el constructor,
            pero se vuelven obligatorios al usar los setters.
        """
        self.swagger_types = {
            'card_number': str,
            'expire_month': int,
            'expire_year': int,
            'card_holder': str
        }

        self.attribute_map = {
            'card_number': 'cardNumber',
            'expire_month': 'expireMonth',
            'expire_year': 'expireYear',
            'card_holder': 'cardHolder'
        }
        self._card_number = card_number
        self._expire_month = expire_month
        self._expire_year = expire_year
        self._card_holder = card_holder

    @classmethod
    def from_dict(cls, dikt) -> 'PaymentMethod':
        """
        Crea una instancia de PaymentMethod desde un diccionario.
        
        Deserializa un diccionario (típicamente desde JSON) en un objeto PaymentMethod,
        mapeando correctamente los nombres de campos JSON a atributos Python.
        
        Args:
            dikt (dict): Diccionario con los datos del método de pago.
                        Debe contener: cardNumber, expireMonth, expireYear, cardHolder.
        
        Returns:
            PaymentMethod: Nueva instancia con los datos deserializados.
        
        Example:
            >>> data = {
            ...     "cardNumber": "**** **** **** 1234",
            ...     "expireMonth": 12,
            ...     "expireYear": 2025,
            ...     "cardHolder": "Juan Pérez"
            ... }
            >>> payment = PaymentMethod.from_dict(data)
        """
        return util.deserialize_model(dikt, cls)

    @property
    def card_number(self) -> str:
        """Gets the card_number of this PaymentMethod.

        Masked card number.  # noqa: E501

        :return: The card_number of this PaymentMethod.
        :rtype: str
        """
        return self._card_number

    @card_number.setter
    def card_number(self, card_number: str):
        """Sets the card_number of this PaymentMethod.

        Masked card number.  # noqa: E501

        :param card_number: The card_number of this PaymentMethod.
        :type card_number: str
        """
        if card_number is None:
            raise ValueError("Invalid value for `card_number`, must not be `None`")  # noqa: E501

        self._card_number = card_number

    @property
    def expire_month(self) -> int:
        """Gets the expire_month of this PaymentMethod.

        Expire month of the card.  # noqa: E501

        :return: The expire_month of this PaymentMethod.
        :rtype: int
        """
        return self._expire_month

    @expire_month.setter
    def expire_month(self, expire_month: int):
        """Sets the expire_month of this PaymentMethod.

        Expire month of the card.  # noqa: E501

        :param expire_month: The expire_month of this PaymentMethod.
        :type expire_month: int
        """
        if expire_month is None:
            raise ValueError("Invalid value for `expire_month`, must not be `None`")  # noqa: E501

        self._expire_month = expire_month

    @property
    def expire_year(self) -> int:
        """Gets the expire_year of this PaymentMethod.

        Expire year of the card.  # noqa: E501

        :return: The expire_year of this PaymentMethod.
        :rtype: int
        """
        return self._expire_year

    @expire_year.setter
    def expire_year(self, expire_year: int):
        """Sets the expire_year of this PaymentMethod.

        Expire year of the card.  # noqa: E501

        :param expire_year: The expire_year of this PaymentMethod.
        :type expire_year: int
        """
        if expire_year is None:
            raise ValueError("Invalid value for `expire_year`, must not be `None`")  # noqa: E501

        self._expire_year = expire_year

    @property
    def card_holder(self) -> str:
        """Gets the card_holder of this PaymentMethod.

        Name of the card  # noqa: E501

        :return: The card_holder of this PaymentMethod.
        :rtype: str
        """
        return self._card_holder

    @card_holder.setter
    def card_holder(self, card_holder: str):
        """Sets the card_holder of this PaymentMethod.

        Name of the card  # noqa: E501

        :param card_holder: The card_holder of this PaymentMethod.
        :type card_holder: str
        """
        if card_holder is None:
            raise ValueError("Invalid value for `card_holder`, must not be `None`")  # noqa: E501

        self._card_holder = card_holder
