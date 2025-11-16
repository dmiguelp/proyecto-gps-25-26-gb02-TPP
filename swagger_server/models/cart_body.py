# coding: utf-8
"""
Modelo CartBody - Cuerpo de petición para operaciones de carrito.

Este módulo define el modelo de datos para las peticiones de adición de productos
al carrito de compras. Soporta tres tipos de productos: canciones, álbumes y
merchandising, permitiendo especificar cantidades para el merchandising.

Características:
    - Modelo flexible que acepta diferentes tipos de productos
    - Validación de cantidades mínimas para merchandising
    - Serialización/deserialización JSON automática
    - Integración con Swagger/OpenAPI

Uso típico:
    El frontend envía este objeto en peticiones POST /cart para añadir productos:
        - Para canciones: {"songId": 42}
        - Para álbumes: {"albumId": 10}
        - Para merch: {"merchId": 5, "unidades": 3}

Restricciones:
    - Debe proporcionar exactamente uno de: songId, albumId o merchId
    - unidades debe ser >= 1 (solo aplica a merch)
    - La validación de exclusividad se realiza en el controlador

Schema OpenAPI:
    Definido en swagger.yaml bajo components/schemas/cart_body
"""

from __future__ import absolute_import
from swagger_server.models.base_model_ import Model
from swagger_server import util


class CartBody(Model):
    """
    Modelo para el cuerpo de petición al añadir productos al carrito.
    
    Representa los datos necesarios para añadir un producto (canción, álbum o merch)
    al carrito de compras de un usuario. Solo uno de los IDs debe estar presente.
    
    Attributes:
        song_id (int, optional): ID de la canción a añadir. None si no es canción.
        album_id (int, optional): ID del álbum a añadir. None si no es álbum.
        merch_id (int, optional): ID del merchandising a añadir. None si no es merch.
        unidades (int): Cantidad de unidades a añadir. Solo aplica a merch.
                       Default: 1. Mínimo: 1.
    
    JSON Mapping:
        - song_id ↔ songId
        - album_id ↔ albumId
        - merch_id ↔ merchId
        - unidades ↔ unidades
    
    Examples:
        >>> # Crear instancia para añadir canción
        >>> cart_item = CartBody(song_id=42)
        
        >>> # Crear instancia para añadir merch con cantidad
        >>> cart_item = CartBody(merch_id=10, unidades=3)
        
        >>> # Deserializar desde JSON
        >>> data = {"albumId": 5}
        >>> cart_item = CartBody.from_dict(data)
    
    Validation:
        - unidades debe ser >= 1 (validado en el setter)
        - Solo uno de song_id, album_id, merch_id debe estar presente (validado en controlador)
    """

    def __init__(self, song_id: int = None, album_id: int = None, merch_id: int = None, unidades: int = 1):  # noqa: E501
        """
        Constructor del modelo CartBody.
        
        Inicializa una instancia de CartBody con los datos del producto a añadir al carrito.
        Configura los tipos de datos y el mapeo entre atributos Python y JSON.
        
        Args:
            song_id (int, optional): ID de la canción a añadir. Default: None.
            album_id (int, optional): ID del álbum a añadir. Default: None.
            merch_id (int, optional): ID del merchandising a añadir. Default: None.
            unidades (int, optional): Cantidad de unidades (solo merch). Default: 1.
        
        Note:
            Solo uno de los IDs (song_id, album_id, merch_id) debería tener valor.
            Esta validación se realiza en el controlador, no en el modelo.
        """
        self.swagger_types = {
            'song_id': int,
            'album_id': int,
            'merch_id': int,
            'unidades': int
        }

        self.attribute_map = {
            'song_id': 'songId',
            'album_id': 'albumId',
            'merch_id': 'merchId',
            'unidades': 'unidades'
        }

        self._song_id = song_id
        self._album_id = album_id
        self._merch_id = merch_id
        self._unidades = unidades or 1

    @classmethod
    def from_dict(cls, dikt) -> 'CartBody':
        """
        Crea una instancia de CartBody desde un diccionario.
        
        Deserializa un diccionario (típicamente desde JSON) en un objeto CartBody,
        mapeando correctamente los nombres de campos JSON a atributos Python.
        
        Args:
            dikt (dict): Diccionario con los datos del producto.
                        Puede contener: songId, albumId, merchId, unidades.
        
        Returns:
            CartBody: Nueva instancia con los datos deserializados.
        
        Example:
            >>> data = {"merchId": 5, "unidades": 2}
            >>> cart_item = CartBody.from_dict(data)
            >>> cart_item.merch_id  # 5
            >>> cart_item.unidades  # 2
        """
        return util.deserialize_model(dikt, cls)

    @property
    def song_id(self) -> int:
        return self._song_id

    @song_id.setter
    def song_id(self, song_id: int):
        self._song_id = song_id

    @property
    def album_id(self) -> int:
        return self._album_id

    @album_id.setter
    def album_id(self, album_id: int):
        self._album_id = album_id

    @property
    def merch_id(self) -> int:
        return self._merch_id

    @merch_id.setter
    def merch_id(self, merch_id: int):
        self._merch_id = merch_id

    @property
    def unidades(self) -> int:
        return self._unidades

    @unidades.setter
    def unidades(self, unidades: int):
        """
        Establece la cantidad de unidades del producto.
        
        Valida que la cantidad sea al menos 1. Si se proporciona None o un valor
        menor a 1, establece el valor por defecto de 1.
        
        Args:
            unidades (int): Cantidad de unidades a establecer.
        
        Raises:
            ValueError: Si se proporciona un valor menor a 1 (opcional, actualmente
                       se asigna 1 por defecto en lugar de lanzar excepción).
        
        Note:
            Este campo solo tiene sentido para productos de tipo merch.
            Para canciones y álbumes se ignora.
        """
        if unidades is not None and unidades < 1:
            raise ValueError("La cantidad debe ser al menos 1")
        self._unidades = unidades or 1
