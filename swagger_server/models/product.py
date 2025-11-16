# coding: utf-8
"""
Modelo Product - Representación unificada de productos de la tienda.

Este módulo define el modelo de datos para todos los tipos de productos disponibles
en la tienda de OverSounds: canciones, álbumes y merchandising. Utiliza un único
modelo polimórfico que puede representar cualquier tipo de producto.

Características:
    - Modelo polimórfico para 3 tipos de productos (canción, álbum, merch)
    - Campos específicos por tipo (ej: duration solo para canciones)
    - Información rica de metadatos (artista, colaboradores, género, portada)
    - Serialización/deserialización JSON automática
    - Integración con microservicio TyA (Temas y Autores)

Tipos de producto:
    1. Canción: Tiene songId, albumId (opcional), duration, genre
    2. Álbum: Tiene albumId, song_list (lista de canciones), genre
    3. Merchandising: Tiene merchId, genre="Merch"

Campos comunes:
    - name: Nombre del producto
    - price: Precio en formato decimal
    - description: Descripción detallada
    - artist: ID del artista principal (como string)
    - colaborators: Lista de IDs de colaboradores
    - release_date: Fecha de lanzamiento
    - cover: Imagen de portada en base64

Schema OpenAPI:
    Definido en swagger.yaml bajo components/schemas/Product

Data Flow:
    TyA (microservicio) → Product (modelo) → Frontend (JSON)
    El modelo actúa como capa de transformación entre servicios.
"""

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class Product(Model):
    """
    Modelo unificado de producto para la tienda OverSounds.
    
    Representa cualquier producto vendible: canciones, álbumes o merchandising.
    Utiliza un diseño polimórfico donde los campos específicos de tipo se
    establecen en None para productos que no los utilizan.
    
    Identificación de tipo:
        - Si song_id != None → Canción
        - Si album_id != None → Álbum  
        - Si merch_id != None → Merchandising
    
    Attributes:
        song_id (int, optional): ID de la canción. None si no es canción.
        album_id (int, optional): ID del álbum. None si no es álbum (o ID del álbum para canciones).
        merch_id (int, optional): ID del merchandising. None si no es merch.
        name (str): Nombre/título del producto. Requerido.
        price (float): Precio en unidades monetarias. Requerido.
        description (str): Descripción del producto. Requerido.
        artist (str): ID del artista principal (almacenado como string). Requerido.
        colaborators (List[int]): Lista de IDs de artistas colaboradores. Requerido.
        release_date (datetime, optional): Fecha de lanzamiento del producto.
        duration (int, optional): Duración en segundos (solo canciones).
        genre (str, optional): Género musical o "Merch" para merchandising.
        cover (str): Imagen de portada codificada en base64. Requerido.
        song_list (List[int], optional): Lista de IDs de canciones (solo álbumes).
    
    JSON Mapping:
        - song_id ↔ songId
        - album_id ↔ albumId
        - merch_id ↔ merchId
        - release_date ↔ releaseDate
        - song_list ↔ songList
        - (otros campos mantienen el mismo nombre)
    
    Examples:
        >>> # Canción
        >>> song = Product(
        ...     song_id=42,
        ...     album_id=10,
        ...     name="Bohemian Rhapsody",
        ...     price=1.99,
        ...     description="Epic rock ballad",
        ...     artist="12",
        ...     colaborators=[],
        ...     duration=354,
        ...     genre="Rock",
        ...     cover="data:image/png;base64,..."
        ... )
        
        >>> # Álbum
        >>> album = Product(
        ...     album_id=10,
        ...     name="A Night at the Opera",
        ...     price=9.99,
        ...     description="Classic album",
        ...     artist="12",
        ...     colaborators=[],
        ...     song_list=[42, 43, 44],
        ...     genre="Rock",
        ...     cover="data:image/png;base64,..."
        ... )
        
        >>> # Merchandising
        >>> merch = Product(
        ...     merch_id=5,
        ...     name="Band T-Shirt",
        ...     price=24.99,
        ...     description="Official merchandise",
        ...     artist="12",
        ...     colaborators=[],
        ...     genre="Merch",
        ...     cover="data:image/png;base64,..."
        ... )
    
    Validation:
        Campos obligatorios:
            - name, price, description, artist, colaborators, cover
        
        Campos opcionales:
            - song_id, album_id, merch_id (al menos uno debería tener valor)
            - release_date, duration, genre, song_list
    
    Note:
        Este modelo es generado automáticamente por Swagger Codegen.
        Los tipos en colaborators y song_list están definidos como List[int]
        pero en la práctica se almacenan como strings en algunas operaciones.
    """
    def __init__(self, song_id: int=None, album_id: int=None, merch_id: int=None, name: str=None, price: float=None, description: str=None, artist: str=None, colaborators: List[int]=None, release_date: datetime=None, duration: int=None, genre: str=None, cover: str=None, song_list: List[int]=None):  # noqa: E501
        """
        Constructor del modelo Product.
        
        Inicializa una instancia de Product con todos sus atributos.
        Configura los tipos de datos y el mapeo entre atributos Python y JSON.
        
        Args:
            song_id (int, optional): ID de la canción (None si no es canción).
            album_id (int, optional): ID del álbum (None si no es álbum).
            merch_id (int, optional): ID del merchandising (None si no es merch).
            name (str): Nombre/título del producto.
            price (float): Precio del producto.
            description (str): Descripción del producto.
            artist (str): ID del artista principal (como string).
            colaborators (List[int]): Lista de IDs de colaboradores.
            release_date (datetime, optional): Fecha de lanzamiento.
            duration (int, optional): Duración en segundos (solo canciones).
            genre (str, optional): Género musical o "Merch".
            cover (str): Portada en formato base64.
            song_list (List[int], optional): Lista de canciones (solo álbumes).
        
        Note:
            Para crear un producto válido, debe tener al menos uno de:
            song_id, album_id, o merch_id con valor no None.
        """
        self.swagger_types = {
            'song_id': int,
            'album_id': int,
            'merch_id': int,
            'name': str,
            'price': float,
            'description': str,
            'artist': str,
            'colaborators': List[int],
            'release_date': datetime,
            'duration': int,
            'genre': str,
            'cover': str,
            'song_list': List[int]
        }

        self.attribute_map = {
            'song_id': 'songId',
            'album_id': 'albumId',
            'merch_id': 'merchId',
            'name': 'name',
            'price': 'price',
            'description': 'description',
            'artist': 'artist',
            'colaborators': 'colaborators',
            'release_date': 'releaseDate',
            'duration': 'duration',
            'genre': 'genre',
            'cover': 'cover',
            'song_list': 'songList'
        }
        self._song_id = song_id
        self._album_id = album_id
        self._merch_id = merch_id
        self._name = name
        self._price = price
        self._description = description
        self._artist = artist
        self._colaborators = colaborators
        self._release_date = release_date
        self._duration = duration
        self._genre = genre
        self._cover = cover
        self._song_list = song_list

    @classmethod
    def from_dict(cls, dikt) -> 'Product':
        """
        Crea una instancia de Product desde un diccionario.
        
        Deserializa un diccionario (típicamente desde JSON o respuesta de microservicio)
        en un objeto Product, mapeando correctamente todos los campos.
        
        Args:
            dikt (dict): Diccionario con los datos del producto.
                        Puede contener campos en notación camelCase (JSON)
                        que se mapearán a snake_case (Python).
        
        Returns:
            Product: Nueva instancia con los datos deserializados.
        
        Example:
            >>> data = {
            ...     "songId": 42,
            ...     "name": "Song Title",
            ...     "price": 1.99,
            ...     "artist": "12",
            ...     "colaborators": [5, 8],
            ...     "cover": "data:image/png;base64,...",
            ...     "description": "Great song",
            ...     "duration": 180
            ... }
            >>> product = Product.from_dict(data)
        """
        return util.deserialize_model(dikt, cls)

    @property
    def song_id(self) -> int:
        """Gets the song_id of this Product.

        ID of the Song (NULL if not song)  # noqa: E501

        :return: The song_id of this Product.
        :rtype: int
        """
        return self._song_id

    @song_id.setter
    def song_id(self, song_id: int):
        """Sets the song_id of this Product.

        ID of the Song (NULL if not song)  # noqa: E501

        :param song_id: The song_id of this Product.
        :type song_id: int
        """

        self._song_id = song_id

    @property
    def album_id(self) -> int:
        """Gets the album_id of this Product.

        ID of the Album (NULL if not album)  # noqa: E501

        :return: The album_id of this Product.
        :rtype: int
        """
        return self._album_id

    @album_id.setter
    def album_id(self, album_id: int):
        """Sets the album_id of this Product.

        ID of the Album (NULL if not album)  # noqa: E501

        :param album_id: The album_id of this Product.
        :type album_id: int
        """

        self._album_id = album_id

    @property
    def merch_id(self) -> int:
        """Gets the merch_id of this Product.

        ID of the Merch (NULL if not merch)  # noqa: E501

        :return: The merch_id of this Product.
        :rtype: int
        """
        return self._merch_id

    @merch_id.setter
    def merch_id(self, merch_id: int):
        """Sets the merch_id of this Product.

        ID of the Merch (NULL if not merch)  # noqa: E501

        :param merch_id: The merch_id of this Product.
        :type merch_id: int
        """

        self._merch_id = merch_id

    @property
    def name(self) -> str:
        """Gets the name of this Product.

        Name of the product  # noqa: E501

        :return: The name of this Product.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this Product.

        Name of the product  # noqa: E501

        :param name: The name of this Product.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def price(self) -> float:
        """Gets the price of this Product.

        Price of the Song  # noqa: E501

        :return: The price of this Product.
        :rtype: float
        """
        return self._price

    @price.setter
    def price(self, price: float):
        """Sets the price of this Product.

        Price of the Song  # noqa: E501

        :param price: The price of this Product.
        :type price: float
        """
        if price is None:
            raise ValueError("Invalid value for `price`, must not be `None`")  # noqa: E501

        self._price = price

    @property
    def description(self) -> str:
        """Gets the description of this Product.

        Description of the product  # noqa: E501

        :return: The description of this Product.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description: str):
        """Sets the description of this Product.

        Description of the product  # noqa: E501

        :param description: The description of this Product.
        :type description: str
        """
        if description is None:
            raise ValueError("Invalid value for `description`, must not be `None`")  # noqa: E501

        self._description = description

    @property
    def artist(self) -> str:
        """Gets the artist of this Product.

        Name of the Artist that the product belongs to  # noqa: E501

        :return: The artist of this Product.
        :rtype: str
        """
        return self._artist

    @artist.setter
    def artist(self, artist: str):
        """Sets the artist of this Product.

        Name of the Artist that the product belongs to  # noqa: E501

        :param artist: The artist of this Product.
        :type artist: str
        """
        if artist is None:
            raise ValueError("Invalid value for `artist`, must not be `None`")  # noqa: E501

        self._artist = artist

    @property
    def colaborators(self) -> List[int]:
        """Gets the colaborators of this Product.

        List of Names of Artists who collaborated on the product (only song and album)  # noqa: E501

        :return: The colaborators of this Product.
        :rtype: List[int]
        """
        return self._colaborators

    @colaborators.setter
    def colaborators(self, colaborators: List[int]):
        """Sets the colaborators of this Product.

        List of Names of Artists who collaborated on the product (only song and album)  # noqa: E501

        :param colaborators: The colaborators of this Product.
        :type colaborators: List[int]
        """
        if colaborators is None:
            raise ValueError("Invalid value for `colaborators`, must not be `None`")  # noqa: E501

        self._colaborators = colaborators

    @property
    def release_date(self) -> datetime:
        """Gets the release_date of this Product.

        Date of release of the Song  # noqa: E501

        :return: The release_date of this Product.
        :rtype: datetime
        """
        return self._release_date

    @release_date.setter
    def release_date(self, release_date: datetime):
        """Sets the release_date of this Product.

        Date of release of the Song  # noqa: E501

        :param release_date: The release_date of this Product.
        :type release_date: datetime
        """

        self._release_date = release_date

    @property
    def duration(self) -> int:
        """Gets the duration of this Product.

        Duration of song in seconds (null if not a song)  # noqa: E501

        :return: The duration of this Product.
        :rtype: int
        """
        return self._duration

    @duration.setter
    def duration(self, duration: int):
        """Sets the duration of this Product.

        Duration of song in seconds (null if not a song)  # noqa: E501

        :param duration: The duration of this Product.
        :type duration: int
        """

        self._duration = duration

    @property
    def genre(self) -> str:
        """Gets the genre of this Product.

        Genre of a song (null if not song or album)  # noqa: E501

        :return: The genre of this Product.
        :rtype: str
        """
        return self._genre

    @genre.setter
    def genre(self, genre: str):
        """Sets the genre of this Product.

        Genre of a song (null if not song or album)  # noqa: E501

        :param genre: The genre of this Product.
        :type genre: str
        """

        self._genre = genre

    @property
    def cover(self) -> str:
        """Gets the cover of this Product.

        base64 image of the cover  # noqa: E501

        :return: The cover of this Product.
        :rtype: str
        """
        return self._cover

    @cover.setter
    def cover(self, cover: str):
        """Sets the cover of this Product.

        base64 image of the cover  # noqa: E501

        :param cover: The cover of this Product.
        :type cover: str
        """
        if cover is None:
            raise ValueError("Invalid value for `cover`, must not be `None`")  # noqa: E501

        self._cover = cover

    @property
    def song_list(self) -> List[int]:
        """Gets the song_list of this Product.

        List of the names of songs that an Album has (null if not album)  # noqa: E501

        :return: The song_list of this Product.
        :rtype: List[int]
        """
        return self._song_list

    @song_list.setter
    def song_list(self, song_list: List[int]):
        """Sets the song_list of this Product.

        List of the names of songs that an Album has (null if not album)  # noqa: E501

        :param song_list: The song_list of this Product.
        :type song_list: List[int]
        """

        self._song_list = song_list
