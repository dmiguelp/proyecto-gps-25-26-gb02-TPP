# coding: utf-8
"""
Modelo Purchase - Representación de compras de usuarios.

Este módulo define el modelo de datos para las compras realizadas por usuarios
en el sistema OverSounds. Una compra puede incluir múltiples productos de diferentes
tipos (canciones, álbumes, merchandising) pagados con un único método de pago.

Características:
    - Soporte para compras multi-producto en una sola transacción
    - Asociación con método de pago específico
    - Registro de importe total y fecha de compra
    - Listas separadas por tipo de producto
    - Trazabilidad completa de transacciones

Modelo de negocio:
    Una compra típica representa:
        1. Un usuario realiza una compra
        2. Selecciona productos del carrito (o directamente)
        3. Elige un método de pago
        4. Sistema calcula el total
        5. Se procesa el pago
        6. Se registra la compra con todos los productos

Base de datos:
    Relación con tablas:
        - Compras (registro principal)
        - CancionesCompra (relación N:M con canciones)
        - AlbumesCompra (relación N:M con álbumes)
        - MerchCompra (relación N:M con merchandising)

Schema OpenAPI:
    Definido en swagger.yaml bajo components/schemas/Purchase

Use Case:
    Frontend envía Purchase después de que usuario confirma compra:
        - Incluye todos los IDs de productos seleccionados
        - Importe total calculado
        - Fecha actual de la transacción
        - Método de pago seleccionado
"""

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class Purchase(Model):
    """
    Modelo de compra realizada por un usuario.
    
    Representa una transacción completa que puede incluir múltiples productos
    de diferentes tipos. Asocia los productos comprados con el método de pago
    utilizado y registra el importe y la fecha de la transacción.
    
    Attributes:
        purchase_price (float): Importe total de la compra. Debe incluir el precio
                               de todos los productos en las listas. Requerido.
        purchase_date (datetime): Fecha y hora de la compra. Formato ISO 8601.
                                 Requerido.
        payment_method_id (int): ID del método de pago utilizado. Debe corresponder
                                a un PaymentMethod válido del usuario. Requerido.
        song_ids (List[int], optional): Lista de IDs de canciones compradas.
                                       Puede estar vacía si no se compraron canciones.
        album_ids (List[int], optional): Lista de IDs de álbumes comprados.
                                        Puede estar vacía si no se compraron álbumes.
        merch_ids (List[int], optional): Lista de IDs de merchandising comprado.
                                        Puede estar vacía si no se compró merch.
    
    JSON Mapping:
        - purchase_price ↔ purchasePrice
        - purchase_date ↔ purchaseDate
        - payment_method_id ↔ paymentMethodId
        - song_ids ↔ songIds
        - album_ids ↔ albumIds
        - merch_ids ↔ merchIds
    
    Validation:
        Campos obligatorios:
            - purchase_price (debe ser > 0)
            - purchase_date (no debe ser futura)
            - payment_method_id (debe existir y pertenecer al usuario)
        
        Campos opcionales:
            - song_ids, album_ids, merch_ids
            - Al menos una de las listas debe contener elementos
    
    Examples:
        >>> # Compra de canciones y un álbum
        >>> purchase = Purchase(
        ...     purchase_price=14.97,
        ...     purchase_date=datetime.now(),
        ...     payment_method_id=5,
        ...     song_ids=[1, 2, 5],
        ...     album_ids=[3],
        ...     merch_ids=[]
        ... )
        
        >>> # Compra solo de merchandising
        >>> purchase = Purchase(
        ...     purchase_price=49.99,
        ...     purchase_date=datetime(2024, 11, 16, 14, 30),
        ...     payment_method_id=2,
        ...     song_ids=[],
        ...     album_ids=[],
        ...     merch_ids=[10, 11]
        ... )
        
        >>> # Deserializar desde JSON
        >>> data = {
        ...     "purchasePrice": 29.97,
        ...     "purchaseDate": "2024-11-16T14:30:00Z",
        ...     "paymentMethodId": 3,
        ...     "songIds": [1, 5, 12],
        ...     "albumIds": [2],
        ...     "merchIds": []
        ... }
        >>> purchase = Purchase.from_dict(data)
    
    Business Logic:
        - El purchase_price debería calcularse sumando precios de todos los productos
        - La validación de que payment_method_id pertenece al usuario se hace en controlador
        - Las listas de IDs deben corresponder a productos existentes
        - Después de registrar la compra, típicamente se limpia el carrito
    
    Note:
        Este modelo es generado automáticamente por Swagger Codegen.
        La lógica de validación de precios y productos existe en el controlador.
    """
    def __init__(self, purchase_price: float=None, purchase_date: datetime=None, payment_method_id: int=None, song_ids: List[int]=None, album_ids: List[int]=None, merch_ids: List[int]=None):  # noqa: E501
        """
        Constructor del modelo Purchase.
        
        Inicializa una instancia de Purchase con todos los datos de la compra.
        Configura los tipos de datos y el mapeo entre atributos Python y JSON.
        
        Args:
            purchase_price (float): Importe total de la compra.
            purchase_date (datetime): Fecha y hora de la compra.
            payment_method_id (int): ID del método de pago utilizado.
            song_ids (List[int], optional): Lista de IDs de canciones compradas.
            album_ids (List[int], optional): Lista de IDs de álbumes comprados.
            merch_ids (List[int], optional): Lista de IDs de merchandising comprado.
        
        Note:
            Las listas de IDs pueden ser None o listas vacías.
            Al menos una debería contener elementos para una compra válida.
        """
        self.swagger_types = {
            'purchase_price': float,
            'purchase_date': datetime,
            'payment_method_id': int,
            'song_ids': List[int],
            'album_ids': List[int],
            'merch_ids': List[int]
        }

        self.attribute_map = {
            'purchase_price': 'purchasePrice',
            'purchase_date': 'purchaseDate',
            'payment_method_id': 'paymentMethodId',
            'song_ids': 'songIds',
            'album_ids': 'albumIds',
            'merch_ids': 'merchIds'
        }
        self._purchase_price = purchase_price
        self._purchase_date = purchase_date
        self._payment_method_id = payment_method_id
        self._song_ids = song_ids
        self._album_ids = album_ids
        self._merch_ids = merch_ids

    @classmethod
    def from_dict(cls, dikt) -> 'Purchase':
        """
        Crea una instancia de Purchase desde un diccionario.
        
        Deserializa un diccionario (típicamente desde JSON) en un objeto Purchase,
        mapeando correctamente todos los campos de la compra.
        
        Args:
            dikt (dict): Diccionario con los datos de la compra.
                        Debe contener purchasePrice, purchaseDate, paymentMethodId.
                        Opcionalmente: songIds, albumIds, merchIds.
        
        Returns:
            Purchase: Nueva instancia con los datos deserializados.
        
        Example:
            >>> data = {
            ...     "purchasePrice": 29.97,
            ...     "purchaseDate": "2024-11-16T14:30:00Z",
            ...     "paymentMethodId": 3,
            ...     "songIds": [1, 5, 12],
            ...     "albumIds": [2],
            ...     "merchIds": []
            ... }
            >>> purchase = Purchase.from_dict(data)
        """
        return util.deserialize_model(dikt, cls)

    @property
    def purchase_price(self) -> float:
        """Gets the purchase_price of this Purchase.

        Price of the Song  # noqa: E501

        :return: The purchase_price of this Purchase.
        :rtype: float
        """
        return self._purchase_price

    @purchase_price.setter
    def purchase_price(self, purchase_price: float):
        """Sets the purchase_price of this Purchase.

        Price of the Song  # noqa: E501

        :param purchase_price: The purchase_price of this Purchase.
        :type purchase_price: float
        """
        if purchase_price is None:
            raise ValueError("Invalid value for `purchase_price`, must not be `None`")  # noqa: E501

        self._purchase_price = purchase_price

    @property
    def purchase_date(self) -> datetime:
        """Gets the purchase_date of this Purchase.

        Date of the purchase  # noqa: E501

        :return: The purchase_date of this Purchase.
        :rtype: datetime
        """
        return self._purchase_date

    @purchase_date.setter
    def purchase_date(self, purchase_date: datetime):
        """Sets the purchase_date of this Purchase.

        Date of the purchase  # noqa: E501

        :param purchase_date: The purchase_date of this Purchase.
        :type purchase_date: datetime
        """
        if purchase_date is None:
            raise ValueError("Invalid value for `purchase_date`, must not be `None`")  # noqa: E501

        self._purchase_date = purchase_date

    @property
    def payment_method_id(self) -> int:
        """Gets the payment_method_id of this Purchase.

        id of the payment method  # noqa: E501

        :return: The payment_method_id of this Purchase.
        :rtype: int
        """
        return self._payment_method_id

    @payment_method_id.setter
    def payment_method_id(self, payment_method_id: int):
        """Sets the payment_method_id of this Purchase.

        id of the payment method  # noqa: E501

        :param payment_method_id: The payment_method_id of this Purchase.
        :type payment_method_id: int
        """
        if payment_method_id is None:
            raise ValueError("Invalid value for `payment_method_id`, must not be `None`")  # noqa: E501

        self._payment_method_id = payment_method_id

    @property
    def song_ids(self) -> List[int]:
        """Gets the song_ids of this Purchase.

        List of song IDs to purchase  # noqa: E501

        :return: The song_ids of this Purchase.
        :rtype: List[int]
        """
        return self._song_ids

    @song_ids.setter
    def song_ids(self, song_ids: List[int]):
        """Sets the song_ids of this Purchase.

        List of song IDs to purchase  # noqa: E501

        :param song_ids: The song_ids of this Purchase.
        :type song_ids: List[int]
        """
        self._song_ids = song_ids

    @property
    def album_ids(self) -> List[int]:
        """Gets the album_ids of this Purchase.

        List of album IDs to purchase  # noqa: E501

        :return: The album_ids of this Purchase.
        :rtype: List[int]
        """
        return self._album_ids

    @album_ids.setter
    def album_ids(self, album_ids: List[int]):
        """Sets the album_ids of this Purchase.

        List of album IDs to purchase  # noqa: E501

        :param album_ids: The album_ids of this Purchase.
        :type album_ids: List[int]
        """
        self._album_ids = album_ids

    @property
    def merch_ids(self) -> List[int]:
        """Gets the merch_ids of this Purchase.

        List of merch IDs to purchase  # noqa: E501

        :return: The merch_ids of this Purchase.
        :rtype: List[int]
        """
        return self._merch_ids

    @merch_ids.setter
    def merch_ids(self, merch_ids: List[int]):
        """Sets the merch_ids of this Purchase.

        List of merch IDs to purchase  # noqa: E501

        :param merch_ids: The merch_ids of this Purchase.
        :type merch_ids: List[int]
        """
        self._merch_ids = merch_ids
