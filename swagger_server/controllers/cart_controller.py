"""
Controlador de Carrito de Compras.

Este módulo implementa la lógica de negocio para la gestión del carrito de compras
de usuarios en el sistema OverSounds. Permite agregar, consultar y eliminar productos
(canciones, álbumes y merchandising) del carrito.

Características:
    - Gestión de productos de diferentes tipos (canciones, álbumes, merch)
    - Integración con base de datos para persistencia del carrito
    - Integración con microservicio TyA para obtener información de productos
    - Validación de autenticación y autorización de usuarios
    - Manejo de cantidades para productos de merchandising

Dependencias:
    - Microservicio de Autenticación: Validación de tokens y usuarios
    - Microservicio TyA (Temas y Autores): Información detallada de productos
    - Base de datos TPP: Tablas CancionesCarrito, AlbumesCarrito, MerchCarrito

Base de datos:
    Tablas utilizadas:
        - CancionesCarrito (idCancion, idUsuario)
        - AlbumesCarrito (idAlbum, idUsuario)
        - MerchCarrito (idMerch, idUsuario, unidades)
"""

import connexion
import six
import requests

from swagger_server.models.cart_body import CartBody  # noqa: E501
from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.product import Product  # noqa: E501
from swagger_server import util
from swagger_server.dbconx import dbConectar, dbDesconectar
from swagger_server.controllers.config import TYA_SERVICE_URL



def add_to_cart(body=None):
    """
    Añade un producto al carrito del usuario autenticado.
    
    Permite agregar canciones, álbumes o merchandising al carrito de compras.
    Valida que el producto no esté ya en el carrito para evitar duplicados.
    Para merchandising, permite especificar la cantidad de unidades.
    
    Validaciones:
        - El cuerpo de la petición debe ser JSON válido
        - El usuario debe estar autenticado (token válido)
        - Debe proporcionar exactamente uno de: songId, albumId o merchId
        - El producto no debe existir previamente en el carrito
    
    Operaciones en BD:
        - Inserta en CancionesCarrito si es una canción
        - Inserta en AlbumesCarrito si es un álbum
        - Inserta en MerchCarrito (con unidades) si es merchandising
    
    Args:
        body (CartBody, optional): Objeto con el producto a añadir al carrito.
                                   Debe contener uno de: song_id, album_id, merch_id.
                                   Para merch puede incluir 'unidades' (default: 1).
    
    Returns:
        Tuple[Dict|Error, int]: Tupla con respuesta y código HTTP:
            - ({"message": "..."}, 200): Producto añadido exitosamente
            - (Error, 400): Petición inválida (no JSON, producto ya existe, etc.)
            - (Error, 401): Token no encontrado
            - (Error, 403): Usuario no autorizado
            - (Error, 500): Error interno del servidor
    
    Examples:
        Request JSON para añadir canción:
            {"songId": 42}
        
        Request JSON para añadir merch con cantidad:
            {"merchId": 10, "unidades": 3}
    
    Note:
        La transacción se realiza con rollback automático en caso de error.
    """
    print("[DEBUG] add_to_cart: Inicio de la función")
    db_conexion = None
    try:
        print(f"[DEBUG] add_to_cart: Verificando si la petición es JSON")
        if not connexion.request.is_json:
            print("[DEBUG] add_to_cart: ERROR - La petición no es JSON")
            return Error(code="400", message="El cuerpo de la petición no es JSON").to_dict(), 400
        
        print(f"[DEBUG] add_to_cart: Parseando body desde JSON")
        body = CartBody.from_dict(connexion.request.get_json())
        print(f"[DEBUG] add_to_cart: Body parseado - song_id={body.song_id}, album_id={body.album_id}, merch_id={body.merch_id}")

        # Obtener user_id del contexto (ya validado por check_oversound_auth)
        print("[DEBUG] add_to_cart: Obteniendo user_id del contexto")
        print(f"[DEBUG] add_to_cart: connexion.context completo = {connexion.context}")
        user_info = connexion.context.get('token_info')
        print(f"[DEBUG] add_to_cart: user_info del contexto = {user_info}")
        if user_info is None:
            print("[DEBUG] add_to_cart: ERROR CRÍTICO - user_info es None")
            return Error(code="401", message="No se pudo obtener información del usuario autenticado").to_dict(), 401
        user_id = user_info.get('userId') or user_info.get('id')
        print(f"[DEBUG] add_to_cart: user_id obtenido = {user_id}")

        print("[DEBUG] add_to_cart: Conectando a la base de datos")
        db_conexion = dbConectar()
        if db_conexion is None:
            print("[DEBUG] add_to_cart: ERROR - No se pudo conectar a la base de datos")
            return Error(code="503", message="Error al conectar con la base de datos").to_dict(), 503
        cursor = db_conexion.cursor()
        print("[DEBUG] add_to_cart: Conexión establecida")

        if body.song_id:
            print(f"[DEBUG] add_to_cart: Procesando canción con ID {body.song_id}")
            cursor.execute("SELECT 1 FROM CancionesCarrito WHERE idCancion = %s AND idUsuario = %s",
                           (body.song_id, user_id))
            if cursor.fetchone():
                print(f"[DEBUG] add_to_cart: ERROR - La canción {body.song_id} ya está en el carrito")
                return Error(code="400", message="La canción ya está en el carrito").to_dict(), 400
            print(f"[DEBUG] add_to_cart: Insertando canción en el carrito")
            cursor.execute("INSERT INTO CancionesCarrito (idCancion, idUsuario) VALUES (%s, %s)",
                           (body.song_id, user_id))
            print(f"[DEBUG] add_to_cart: Canción insertada correctamente")

        elif body.album_id:
            print(f"[DEBUG] add_to_cart: Procesando álbum con ID {body.album_id}")
            cursor.execute("SELECT 1 FROM AlbumesCarrito WHERE idAlbum = %s AND idUsuario = %s",
                           (body.album_id, user_id))
            if cursor.fetchone():
                print(f"[DEBUG] add_to_cart: ERROR - El álbum {body.album_id} ya está en el carrito")
                return Error(code="400", message="El álbum ya está en el carrito").to_dict(), 400
            print(f"[DEBUG] add_to_cart: Insertando álbum en el carrito")
            cursor.execute("INSERT INTO AlbumesCarrito (idAlbum, idUsuario) VALUES (%s, %s)",
                           (body.album_id, user_id))
            print(f"[DEBUG] add_to_cart: Álbum insertado correctamente")

        elif body.merch_id:
            print(f"[DEBUG] add_to_cart: Procesando merch con ID {body.merch_id}, unidades={body.unidades}")
            cursor.execute("SELECT 1 FROM MerchCarrito WHERE idMerch = %s AND idUsuario = %s",
                           (body.merch_id, user_id))
            if cursor.fetchone():
                print(f"[DEBUG] add_to_cart: ERROR - El merch {body.merch_id} ya está en el carrito")
                return Error(code="400", message="El artículo ya está en el carrito").to_dict(), 400
            print(f"[DEBUG] add_to_cart: Insertando merch en el carrito")
            cursor.execute("INSERT INTO MerchCarrito (idMerch, idUsuario, unidades) VALUES (%s, %s, %s)",
                           (body.merch_id, user_id, body.unidades))
            print(f"[DEBUG] add_to_cart: Merch insertado correctamente")

        else:
            print("[DEBUG] add_to_cart: ERROR - No se proporcionó songId, albumId ni merchId")
            return Error(code="400", message="Debes proporcionar songId, albumId o merchId").to_dict(), 400
        
        print("[DEBUG] add_to_cart: Haciendo commit de la transacción")
        db_conexion.commit()
        cursor.close()
        print("[DEBUG] add_to_cart: Producto añadido exitosamente")
        return {"message": "Producto añadido al carrito correctamente"}, 200

    except Exception as e:
        if db_conexion:
            db_conexion.rollback()
        print(f"[DEBUG] add_to_cart: EXCEPCIÓN - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Error(code="500", message=str(e)).to_dict(), 500

    finally:
        if db_conexion:
            dbDesconectar(db_conexion)



def get_cart_products():
    """
    Obtiene todos los productos del carrito del usuario autenticado.
    
    Consulta las tres tablas de carrito (canciones, álbumes y merch) y obtiene
    la información detallada de cada producto desde el microservicio TyA.
    Construye objetos Product completos con toda la información necesaria para
    mostrar en el frontend.
    
    Flujo de operación:
        1. Valida el token del usuario
        2. Consulta IDs de productos en las tablas de carrito
        3. Para cada ID, realiza petición HTTP al microservicio TyA
        4. Mapea la respuesta a objetos Product del modelo
        5. Retorna lista de productos con información completa
    
    Integración con TyA:
        - GET /song/{id}: Información de canciones
        - GET /album/{id}: Información de álbumes
        - GET /merch/{id}: Información de merchandising
    
    Manejo de errores:
        - Errores de peticiones HTTP a TyA se capturan individualmente
        - Productos que fallan se omiten de la respuesta (no bloquean el resto)
        - Errores se registran en consola con print()
    
    Returns:
        Tuple[List[Dict]|Error, int]: Tupla con respuesta y código HTTP:
            - ([{product1}, {product2}, ...], 200): Lista de productos (puede estar vacía)
            - (Error, 401): Token no encontrado
            - (Error, 403): Usuario no autorizado
            - (Error, 500): Error interno del servidor o BD
    
    Note:
        La función es resiliente: si falla la obtención de algún producto
        individual, continúa con los demás en lugar de fallar completamente.
        
    Performance:
        Realiza múltiples peticiones HTTP síncronas. Para carritos grandes,
        considerar implementación con peticiones asíncronas o batch.
    """
    print("[DEBUG] get_cart_products: Inicio de la función")
    db_conexion = None
    try:
        # Obtener user_id del contexto (ya validado por check_oversound_auth)
        print("[DEBUG] get_cart_products: Obteniendo user_id del contexto")
        user_info = connexion.context.get('token_info')
        user_id = user_info.get('userId') or user_info.get('id')
        print(f"[DEBUG] get_cart_products: user_id obtenido = {user_id}")

        print("[DEBUG] get_cart_products: Conectando a la base de datos")
        db_conexion = dbConectar()
        if db_conexion is None:
            print("[DEBUG] get_cart_products: ERROR - No se pudo conectar a la base de datos")
            return Error(code="503", message="Error al conectar con la base de datos").to_dict(), 503
        cursor = db_conexion.cursor()
        print("[DEBUG] get_cart_products: Conexión establecida")

        canciones = []
        albumes = []
        merchs = []
        productos = []
        
        # Canciones
        print("[DEBUG] get_cart_products: Consultando canciones en el carrito")
        cursor.execute("""
            SELECT c.idCancion
            FROM CancionesCarrito c
            WHERE c.idUsuario = %s
        """, (user_id,))
        for row in cursor.fetchall():
            canciones.append(row[0])
        print(f"[DEBUG] get_cart_products: {len(canciones)} canciones encontradas: {canciones}")
            
        # Álbumes
        print("[DEBUG] get_cart_products: Consultando álbumes en el carrito")
        cursor.execute("""
            SELECT a.idAlbum
            FROM AlbumesCarrito a
            WHERE a.idUsuario = %s
        """, (user_id,))
        for row in cursor.fetchall():
            albumes.append(row[0])
        print(f"[DEBUG] get_cart_products: {len(albumes)} álbumes encontrados: {albumes}")

        # Merch
        print("[DEBUG] get_cart_products: Consultando merch en el carrito")
        cursor.execute("""
            SELECT m.idMerch, m.unidades
            FROM MerchCarrito m
            WHERE m.idUsuario = %s
        """, (user_id,))
        for row in cursor.fetchall():
            merchs.append((row[0], row[1]))
        print(f"[DEBUG] get_cart_products: {len(merchs)} items de merch encontrados: {merchs}")

        # Resolvemos IDs de canciones, albumes y merch usando el microservicio TyA.
        print(f"[DEBUG] get_cart_products: Resolviendo información de productos desde TyA ({TYA_SERVICE_URL})")
        for cancion_id in canciones:
            try:
                print(f"[DEBUG] get_cart_products: Obteniendo canción {cancion_id} desde TyA")
                response = requests.get(f"{TYA_SERVICE_URL}/song/{cancion_id}", timeout=3)
                print(f"[DEBUG] get_cart_products: Respuesta de TyA para canción {cancion_id}: status={response.status_code}")
                if response.status_code == 200:
                    producto_data = response.json()
                    producto_schema = Product()
                    producto_schema.song_id = producto_data.get("songId")
                    producto_schema.name = producto_data.get("title")
                    producto_schema.description = producto_data.get("description")
                    producto_schema.price = producto_data.get("price")
                    producto_schema.artist = producto_data.get("artistId", 0)
                    producto_schema.colaborators = producto_data.get("collaborators", [])
                    producto_schema.genre = producto_data.get("genres", [0])[0] if producto_data.get("genres") else 0
                    producto_schema.duration = producto_data.get("duration", 0)
                    producto_schema.cover = producto_data.get("cover")
                    producto_schema.release_date = producto_data.get("releaseDate")
                    producto_schema.album_id = producto_data.get("albumId")
                    productos.append(producto_schema)
                    print(f"[DEBUG] get_cart_products: Canción {cancion_id} añadida a productos")
            except Exception as e:
                print(f"[DEBUG] get_cart_products: ERROR al obtener canción {cancion_id}: {type(e).__name__}: {e}")

        for album_id in albumes:
            try:
                print(f"[DEBUG] get_cart_products: Obteniendo álbum {album_id} desde TyA")
                response = requests.get(f"{TYA_SERVICE_URL}/album/{album_id}", timeout=3)
                print(f"[DEBUG] get_cart_products: Respuesta de TyA para álbum {album_id}: status={response.status_code}")
                if response.status_code == 200:
                    producto_data = response.json()
                    producto_schema = Product()
                    producto_schema.album_id = producto_data.get("albumId")
                    producto_schema.name = producto_data.get("title")
                    producto_schema.description = producto_data.get("description")
                    producto_schema.price = producto_data.get("price")
                    producto_schema.artist = producto_data.get("artistId", 0)
                    producto_schema.colaborators = producto_data.get("collaborators", [])
                    producto_schema.genre = producto_data.get("genres", [0])[0] if producto_data.get("genres") else 0
                    producto_schema.song_list = producto_data.get("songs", [])
                    producto_schema.cover = producto_data.get("cover")
                    producto_schema.release_date = producto_data.get("releaseDate")
                    productos.append(producto_schema)
                    print(f"[DEBUG] get_cart_products: Álbum {album_id} añadido a productos")
            except Exception as e:
                print(f"[DEBUG] get_cart_products: ERROR al obtener álbum {album_id}: {type(e).__name__}: {e}")

        for merch_tuple in merchs:
            merch_id = merch_tuple[0]  # El primer elemento es el ID
            try:
                print(f"[DEBUG] get_cart_products: Obteniendo merch {merch_id} desde TyA")
                response = requests.get(f"{TYA_SERVICE_URL}/merch/{merch_id}", timeout=3)
                print(f"[DEBUG] get_cart_products: Respuesta de TyA para merch {merch_id}: status={response.status_code}")
                if response.status_code == 200:
                    producto_data = response.json()
                    producto_schema = Product()
                    producto_schema.merch_id = producto_data.get("merchId")
                    producto_schema.name = producto_data.get("title")
                    producto_schema.description = producto_data.get("description")
                    producto_schema.price = producto_data.get("price")
                    producto_schema.artist = producto_data.get("artistId", 0)
                    producto_schema.colaborators = producto_data.get("collaborators", [])
                    producto_schema.genre = None  # Merch no tiene género en TyA
                    producto_schema.cover = producto_data.get("cover")
                    producto_schema.release_date = producto_data.get("releaseDate")
                    productos.append(producto_schema)
                    print(f"[DEBUG] get_cart_products: Merch {merch_id} añadido a productos")
            except Exception as e:
                print(f"[DEBUG] get_cart_products: ERROR al obtener merch {merch_id}: {type(e).__name__}: {e}")

        cursor.close()
        print(f"[DEBUG] get_cart_products: Total de productos a retornar: {len(productos)}")
        return [p.to_dict() for p in productos], 200

    except Exception as e:
        print(f"[DEBUG] get_cart_products: EXCEPCIÓN - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Error(code="500", message=str(e)).to_dict(), 500
    finally:
        if db_conexion:
            dbDesconectar(db_conexion)


def remove_from_cart(product_id, type=None):
    """
    Elimina un producto del carrito del usuario autenticado.
    
    Permite eliminar canciones, álbumes o merchandising del carrito.
    Si no se especifica 'type', intenta eliminar el producto de todas las tablas.
    
    Tipos de producto soportados:
        - "song" o "0": Canción
        - "album" o "1": Álbum
        - "merch" o "2": Merchandising
        - None: Busca en todas las tablas
    
    Operaciones en BD:
        - DELETE en CancionesCarrito si type es "song" o "0"
        - DELETE en AlbumesCarrito si type es "album" o "1"
        - DELETE en MerchCarrito si type es "merch" o "2"
        - Si type es None, intenta eliminar de las 3 tablas
    
    Args:
        product_id (int): ID del producto a eliminar del carrito.
        type (str, optional): Tipo de producto ("song"/"0", "album"/"1", "merch"/"2").
    
    Returns:
        Tuple[Dict|Error, int]: Tupla con respuesta y código HTTP:
            - ({"message": "..."}, 200): Producto eliminado exitosamente
            - (Error, 400): Tipo de producto inválido
            - (Error, 401): Token no encontrado
            - (Error, 403): Usuario no autorizado
            - (Error, 404): Producto no encontrado en el carrito
            - (Error, 500): Error interno del servidor
    
    Examples:
        >>> # Eliminar canción con ID 42
        >>> remove_from_cart(42, "song")
        
        >>> # Eliminar sin especificar tipo (busca automáticamente)
        >>> remove_from_cart(10)
    
    Note:
        - La función verifica que el producto exista en el carrito antes de eliminar
        - Si el producto no está en el carrito, retorna error 404
        - La transacción incluye rollback automático en caso de error
    
    Security:
        Solo elimina productos del carrito del usuario autenticado,
        no puede eliminar productos de carritos de otros usuarios.
    """
    db_conexion = None
    try:
        # --- VERIFICAR TOKEN ---
        # Obtener user_id del contexto (ya validado por check_oversound_auth)
        user_info = connexion.context.get('token_info')
        user_id = user_info.get('userId') or user_info.get('id')
        # --- VERIFICAR TOKEN ---

        # Eliminar producto del carrito del usuario autenticado
        db_conexion = dbConectar()
        if db_conexion is None:
            print("[DEBUG] remove_from_cart: ERROR - No se pudo conectar a la base de datos")
            return Error(code="503", message="Error al conectar con la base de datos").to_dict(), 503
        cursor = db_conexion.cursor()

        # Si no se especifica type, intentar eliminar de todas las tablas
        if type is None:
            deleted = False
            
            # Intentar eliminar de CancionesCarrito
            cursor.execute("DELETE FROM CancionesCarrito WHERE idCancion = %s AND idUsuario = %s",
                           (product_id, user_id))
            if cursor.rowcount > 0:
                deleted = True
            
            # Intentar eliminar de AlbumesCarrito
            if not deleted:
                cursor.execute("DELETE FROM AlbumesCarrito WHERE idAlbum = %s AND idUsuario = %s",
                               (product_id, user_id))
                if cursor.rowcount > 0:
                    deleted = True
            
            # Intentar eliminar de MerchCarrito
            if not deleted:
                cursor.execute("DELETE FROM MerchCarrito WHERE idMerch = %s AND idUsuario = %s",
                               (product_id, user_id))
                if cursor.rowcount > 0:
                    deleted = True
            
            if not deleted:
                return Error(code="404", message="El producto no está en el carrito").to_dict(), 404
        
        elif type == "song" or type == "0":
            # Verificar que la canción existe en el carrito del usuario
            cursor.execute("SELECT 1 FROM CancionesCarrito WHERE idCancion = %s AND idUsuario = %s",
                           (product_id, user_id))
            if not cursor.fetchone():
                return Error(code="404", message="La canción no está en el carrito").to_dict(), 404
            
            cursor.execute("DELETE FROM CancionesCarrito WHERE idCancion = %s AND idUsuario = %s",
                           (product_id, user_id))
        elif type == "album" or type == "1":
            # Verificar que el álbum existe en el carrito del usuario
            cursor.execute("SELECT 1 FROM AlbumesCarrito WHERE idAlbum = %s AND idUsuario = %s",
                           (product_id, user_id))
            if not cursor.fetchone():
                return Error(code="404", message="El álbum no está en el carrito").to_dict(), 404
            
            cursor.execute("DELETE FROM AlbumesCarrito WHERE idAlbum = %s AND idUsuario = %s",
                           (product_id, user_id))
        elif type == "merch" or type == "2":
            # Verificar que el merch existe en el carrito del usuario
            cursor.execute("SELECT 1 FROM MerchCarrito WHERE idMerch = %s AND idUsuario = %s",
                           (product_id, user_id))
            if not cursor.fetchone():
                return Error(code="404", message="El artículo no está en el carrito").to_dict(), 404
            
            cursor.execute("DELETE FROM MerchCarrito WHERE idMerch = %s AND idUsuario = %s",
                           (product_id, user_id))
        else:
            return Error(code="400", message="Tipo de producto inválido").to_dict(), 400
    
        db_conexion.commit()
        cursor.close()

        return {"message": "Producto eliminado del carrito correctamente"}, 200

    except Exception as e:
        if db_conexion:
            db_conexion.rollback()
        print(f"[DEBUG] remove_from_cart: EXCEPCIÓN - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Error(code="500", message=str(e)).to_dict(), 500

    finally:
        if db_conexion:
            dbDesconectar(db_conexion)
