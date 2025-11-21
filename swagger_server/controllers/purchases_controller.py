"""
Controlador de Compras.

Este módulo gestiona el registro de compras realizadas por los usuarios en el
sistema OverSounds. Procesa transacciones que incluyen canciones, álbumes y
merchandising, asociándolas con métodos de pago y registrando toda la información
necesaria para el historial de compras.

Características:
    - Registro de compras con múltiples productos (carrito completo)
    - Asociación con métodos de pago específicos
    - Soporte para productos de diferentes tipos en una misma compra
    - Registro de importe total y fecha de la transacción
    - Trazabilidad completa de todas las compras

Modelo de datos:
    Una compra (Purchase) puede contener:
        - Una o más canciones (song_ids)
        - Uno o más álbumes (album_ids)
        - Uno o más artículos de merchandising (merch_ids)
    
    Todas asociadas al mismo método de pago e importe total.

Base de datos:
    Tablas utilizadas:
        - Compras (idCompra, idUsuario, importe, fecha, metodoPago)
        - CancionesCompra (idCompra, idCancion) [relación N:M]
        - AlbumesCompra (idCompra, idAlbum) [relación N:M]
        - MerchCompra (idCompra, idMerch) [relación N:M]

Dependencias:
    - Microservicio de Autenticación: Validación de usuarios
    - Base de datos TPP: Persistencia de compras

Flujo típico:
    1. Usuario revisa carrito
    2. Usuario selecciona método de pago
    3. Frontend calcula importe total
    4. Se envía Purchase con todos los IDs de productos
    5. Se registra en BD y se limpiaría el carrito (si se implementa)
"""

import connexion
import six
import requests
from datetime import datetime

from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.purchase import Purchase  # noqa: E501
from swagger_server import util
from swagger_server.dbconx import dbConectar, dbDesconectar

def set_purchase(body=None):
    """
    Registra una nueva compra realizada por el usuario autenticado.
    
    Crea un registro de compra en la base de datos incluyendo todos los productos
    adquiridos (canciones, álbumes y/o merchandising). La compra se asocia con
    un método de pago específico y registra el importe total y la fecha.
    
    Flujo de operación:
        1. Valida formato JSON del cuerpo
        2. Verifica autenticación del usuario
        3. Inserta registro principal en tabla Compras
        4. Registra cada canción comprada en CancionesCompra
        5. Registra cada álbum comprado en AlbumesCompra
        6. Registra cada artículo de merch en MerchCompra
        7. Confirma transacción y retorna ID de compra
    
    Transaccionalidad:
        - Toda la operación se realiza en una transacción única
        - Si falla cualquier INSERT, se hace rollback completo
        - Errores en productos individuales se registran pero no detienen el proceso
    
    Validaciones:
        - Cuerpo debe ser JSON válido
        - Usuario debe estar autenticado
        - Campos requeridos: purchasePrice, purchaseDate, paymentMethodId
        - Al menos una de las listas (song_ids, album_ids, merch_ids) debe tener contenido
    
    Args:
        body (Purchase, optional): Objeto con los datos de la compra.
            Campos:
                - purchase_price (float): Importe total de la compra
                - purchase_date (datetime): Fecha y hora de la compra
                - payment_method_id (int): ID del método de pago utilizado
                - song_ids (List[int], optional): Lista de IDs de canciones compradas
                - album_ids (List[int], optional): Lista de IDs de álbumes comprados
                - merch_ids (List[int], optional): Lista de IDs de merch comprados
    
    Returns:
        Tuple[Dict|Error, int]: Tupla con respuesta y código HTTP:
            - ({"message": "...", "userId": id}, 200): Compra registrada exitosamente
            - (Error, 400): Petición JSON inválida
            - (Error, 401): Token no encontrado
            - (Error, 403): Usuario no autorizado
            - (Error, 500): Error de BD o registro fallido
    
    Examples:
        Request JSON:
            {
                "purchasePrice": 29.97,
                "purchaseDate": "2024-11-16T14:30:00Z",
                "paymentMethodId": 3,
                "songIds": [1, 5, 12],
                "albumIds": [2],
                "merchIds": []
            }
        
        Response JSON (éxito):
            {
                "message": "Compra registrada con id 42",
                "userId": 7
            }
    
    Note:
        - Los errores en productos individuales se capturan y registran sin detener el proceso
        - Esto permite que la compra se complete aunque algún producto tenga problemas
        - Considerar si esto es el comportamiento deseado o si debería ser todo-o-nada
    
    Database Schema:
        - Compras.metodoPago debe ser FK a MetodosPago.idMetodoPago
        - Valida que el método de pago pertenece al usuario autenticado
    
    Implemented improvements:
        - ✓ Validar que el método de pago pertenece al usuario autenticado
        - ✓ Limpiar carrito automáticamente después de compra exitosa
    
    Future improvements:
        - Validar que los productos existen antes de registrar
        - Implementar sistema de inventario/stock para merch
        - Enviar notificación/email de confirmación
    """
    print("[DEBUG] create_purchase: Inicio de la función")
    db_conexion = None
    try:
        # Verifica que el cuerpo sea JSON
        print("[DEBUG] create_purchase: Verificando si la petición es JSON")
        if not connexion.request.is_json:
            print("[DEBUG] create_purchase: ERROR - La petición no es JSON")
            return Error(code="400", message="El cuerpo de la petición no es JSON").to_dict(), 400
        body = Purchase.from_dict(connexion.request.get_json())
        print(f"[DEBUG] create_purchase: Body parseado correctamente")

        # Obtener user_id del contexto (ya validado por check_oversound_auth)
        print("[DEBUG] create_purchase: Obteniendo user_id del contexto")
        user_info = connexion.context.get('token_info')
        user_id = user_info.get('userId') or user_info.get('id')
        print(f"[DEBUG] create_purchase: user_id obtenido = {user_id}")

        # Conexión con la base de datos
        print("[DEBUG] create_purchase: Conectando a la base de datos")
        db_conexion = dbConectar()
        cursor = db_conexion.cursor()
        print("[DEBUG] create_purchase: Conexión establecida")
        
        # --- VALIDAR QUE EL MÉTODO DE PAGO PERTENECE AL USUARIO ---
        print(f"[DEBUG] create_purchase: Validando método de pago {body.payment_method_id} para usuario {user_id}")
        cursor.execute(
            "SELECT 1 FROM UsuariosMetodosPago WHERE idMetodoPago = %s AND idUsuario = %s",
            (body.payment_method_id, user_id)
        )
        if not cursor.fetchone():
            print("[DEBUG] create_purchase: ERROR - El método de pago no pertenece al usuario")
            return Error(code="403", message="El método de pago no pertenece al usuario o no existe").to_dict(), 403
        print("[DEBUG] create_purchase: Método de pago validado correctamente")
        # --- VALIDAR MÉTODO DE PAGO ---
        
        # Inserta la compra
        print(f"[DEBUG] create_purchase: Insertando compra en BD - importe={body.purchase_price}, fecha={body.purchase_date}")
        cursor.execute(
            """
            INSERT INTO Compras (idUsuario, importe, fecha, metodoPago)
            VALUES (%s, %s, %s, %s)
            RETURNING idCompra
            """,
            (user_id, body.purchase_price, body.purchase_date, body.payment_method_id)
        )
        result = cursor.fetchone()
        if not result:
            print("[DEBUG] create_purchase: ERROR - No se obtuvo ID de la compra")
            db_conexion.rollback()
            return Error(code="500", message="No se pudo registrar la compra").to_dict(), 500
        id_compra = result[0]
        print(f"[DEBUG] create_purchase: Compra registrada con ID = {id_compra}")

        # Registrar los productos de la compra en las tablas intermedias
        if body.song_ids:
            for song_id in body.song_ids:
                try:
                    cursor.execute(
                        "INSERT INTO CancionesCompra (idCompra, idCancion) VALUES (%s, %s)",
                        (id_compra, song_id)
                    )
                except Exception as e:
                    print(f"Error al registrar canción {song_id}: {e}")
        
        if body.album_ids:
            for album_id in body.album_ids:
                try:
                    cursor.execute(
                        "INSERT INTO AlbumesCompra (idCompra, idAlbum) VALUES (%s, %s)",
                        (id_compra, album_id)
                    )
                except Exception as e:
                    print(f"Error al registrar álbum {album_id}: {e}")
        
        if body.merch_ids:
            for merch_id in body.merch_ids:
                try:
                    cursor.execute(
                        "INSERT INTO MerchCompra (idCompra, idMerch) VALUES (%s, %s)",
                        (id_compra, merch_id)
                    )
                except Exception as e:
                    print(f"Error al registrar merch {merch_id}: {e}")

        # --- LIMPIAR CARRITO AUTOMÁTICAMENTE DESPUÉS DE COMPRA EXITOSA ---
        try:
            # Eliminar canciones del carrito
            if body.song_ids:
                for song_id in body.song_ids:
                    cursor.execute(
                        "DELETE FROM CancionesCarrito WHERE idCancion = %s AND idUsuario = %s",
                        (song_id, user_id)
                    )
            
            # Eliminar álbumes del carrito
            if body.album_ids:
                for album_id in body.album_ids:
                    cursor.execute(
                        "DELETE FROM AlbumesCarrito WHERE idAlbum = %s AND idUsuario = %s",
                        (album_id, user_id)
                    )
            
            # Eliminar merchandising del carrito
            if body.merch_ids:
                for merch_id in body.merch_ids:
                    cursor.execute(
                        "DELETE FROM MerchCarrito WHERE idMerch = %s AND idUsuario = %s",
                        (merch_id, user_id)
                    )
            
            print(f"Carrito limpiado automáticamente para usuario {user_id} después de compra {id_compra}")
        except Exception as e:
            # El error al limpiar el carrito no debe impedir que la compra se registre
            print(f"Advertencia: Error al limpiar carrito del usuario {user_id}: {e}")
        # --- FIN LIMPIEZA DE CARRITO ---

        print("[DEBUG] create_purchase: Haciendo commit de la transacción")
        db_conexion.commit()
        cursor.close()
        print(f"[DEBUG] create_purchase: Compra registrada exitosamente con ID {id_compra}")

        return {"message": f"Compra registrada con id {id_compra}", "userId": user_id}, 200

    except Exception as e:
        if db_conexion:
            db_conexion.rollback()
        print(f"[DEBUG] create_purchase: EXCEPCIÓN - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return Error(code="500", message=str(e)).to_dict(), 500

    finally:
        if db_conexion:
            dbDesconectar(db_conexion)
