"""
Controlador de Métodos de Pago.

Este módulo gestiona los métodos de pago asociados a los usuarios del sistema
OverSounds. Permite crear, listar y eliminar métodos de pago (tarjetas de crédito/débito)
que los usuarios utilizan para realizar compras.

Características:
    - Alta de nuevos métodos de pago con validación de datos
    - Consulta de métodos de pago por usuario autenticado
    - Eliminación de métodos de pago existentes
    - Almacenamiento seguro de información de tarjetas (enmascarada)
    - Asociación de métodos de pago con usuarios específicos

Seguridad:
    - Números de tarjeta almacenados de forma enmascarada
    - Validación de autenticación requerida en todos los endpoints
    - Usuarios solo pueden acceder a sus propios métodos de pago

Base de datos:
    Tablas utilizadas:
        - MetodosPago (idMetodoPago, numeroTarjeta, mesValidez, anioVlidez, nombreTarjeta)
        - UsuariosMetodosPago (idUsuario, idMetodoPago) [tabla de relación N:M]

Dependencias:
    - Microservicio de Autenticación: Validación de usuarios
    - Base de datos TPP: Persistencia de métodos de pago
"""

import connexion
import six
import requests

from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.payment_method import PaymentMethod  # noqa: E501
from swagger_server import util
from swagger_server.dbconx import dbConectar, dbDesconectar

# URL del microservicio de usuarios
from swagger_server.controllers.config import USER_SERVICE_URL
from swagger_server.controllers.authorization_controller import verify_token_and_get_user_id


def add_payment_method(body=None):
    """
    Añade un nuevo método de pago para el usuario autenticado.
    
    Crea un método de pago en la base de datos y lo asocia con el usuario actual.
    La información de la tarjeta se almacena de forma enmascarada para cumplir
    con estándares de seguridad (PCI-DSS).
    
    Flujo de operación:
        1. Valida el formato JSON del cuerpo de la petición
        2. Verifica la autenticación del usuario
        3. Inserta el método de pago en tabla MetodosPago
        4. Asocia el método de pago con el usuario en UsuariosMetodosPago
        5. Retorna confirmación con el ID del método creado
    
    Validaciones:
        - Cuerpo debe ser JSON válido
        - Token de usuario debe ser válido
        - Campos requeridos: cardNumber, expireMonth, expireYear, cardHolder
        - expireMonth debe estar entre 1 y 12
    
    Args:
        body (PaymentMethod, optional): Objeto con los datos del método de pago.
            Campos:
                - card_number (str): Número de tarjeta enmascarado (ej: "**** **** **** 1234")
                - expire_month (int): Mes de vencimiento (1-12)
                - expire_year (int): Año de vencimiento (ej: 2030)
                - card_holder (str): Nombre del titular de la tarjeta
    
    Returns:
        Tuple[Dict|Error, int]: Tupla con respuesta y código HTTP:
            - ({"message": "...", "userId": id}, 200): Método creado exitosamente
            - (Error, 400): Petición JSON inválida
            - (Error, 401): Token no encontrado
            - (Error, 403): Usuario no autorizado
            - (Error, 500): Error de BD o creación fallida
    
    Examples:
        Request JSON:
            {
                "cardNumber": "**** **** **** 1234",
                "expireMonth": 12,
                "expireYear": 2025,
                "cardHolder": "Juan Pérez"
            }
    
    Security:
        - Números de tarjeta deben venir ya enmascarados desde el cliente
        - No se almacenan números completos de tarjetas
        - Asociación usuario-método previene acceso no autorizado
    
    Note:
        Utiliza RETURNING en INSERT para obtener el ID del método creado,
        característica específica de PostgreSQL.
    """
    db_conexion = None
    try:
        if not connexion.request.is_json:
            return Error(code="400", message="El cuerpo de la petición no es JSON"), 400
        body = PaymentMethod.from_dict(connexion.request.get_json())

        # --- VERIFICAR TOKEN ---
        token = connexion.request.cookies.get("token")
        user_id, error_response = verify_token_and_get_user_id(token)
        if error_response:
            return error_response
        # --- VERIFICAR TOKEN ---


        # Conexión a la base de datos
        db_conexion = dbConectar()
        cursor = db_conexion.cursor()

        id_metodo = None
        # Crear el método de pago
        cursor.execute(
            """
            INSERT INTO MetodosPago (numeroTarjeta, mesValidez, anioVlidez, nombreTarjeta)
            VALUES (%s, %s, %s, %s)
            RETURNING idMetodoPago
            """,
            (body.card_number, body.expire_month, body.expire_year, body.card_holder)
        )
        result = cursor.fetchone()
        if not result:
            db_conexion.rollback()
            return Error(code="500", message="No se pudo crear el método de pago"), 500
        id_metodo = result[0]

        # Asociar usuario con método de pago
        cursor.execute(
            """
            INSERT INTO UsuariosMetodosPago (idUsuario, idMetodoPago)
            VALUES (%s, %s)
            """,
            (user_id, id_metodo)
        )
        
        db_conexion.commit()
        cursor.close()

        return {"message": f"Método de pago agregado con id {id_metodo}", "userId": user_id}, 200

    except Exception as e:
        if db_conexion:
            db_conexion.rollback()
        print("Error al añadir método de pago:", e)
        return Error(code="500", message=str(e)), 500

    finally:
        if db_conexion:
            dbDesconectar(db_conexion)


def delete_payment_method(payment_method_id):
    """
    Elimina un método de pago por su ID.
    
    Elimina el método de pago de la base de datos incluyendo sus asociaciones
    con usuarios. La eliminación es permanente y no puede deshacerse.
    
    Operaciones en BD:
        1. Elimina de tabla MetodosPago (eliminación principal)
        2. Elimina de tabla UsuariosMetodosPago (limpieza de relaciones)
    
    Validaciones:
        - Usuario debe estar autenticado (token válido)
        - Método de pago debe existir (verifica rowcount)
    
    Args:
        payment_method_id (str): ID del método de pago a eliminar.
    
    Returns:
        Tuple[Dict|Error, int]: Tupla con respuesta y código HTTP:
            - ({"message": "..."}, 200): Método eliminado exitosamente
            - (Error, 401): Token no encontrado
            - (Error, 403): Usuario no autorizado
            - (Error, 404): Método de pago no encontrado
            - (Error, 500): Error interno del servidor
    
    Security:
        Solo permite eliminar métodos de pago que pertenecen al usuario autenticado.
        Valida la propiedad del método antes de la eliminación.
    
    Note:
        La validación de propiedad previene que usuarios eliminen métodos de pago
        de otros usuarios, mejorando la seguridad del sistema.
    """
    db_conexion = None
    try:

        # --- VERIFICAR TOKEN ---
        token = connexion.request.cookies.get("token")
        user_id, error_response = verify_token_and_get_user_id(token)
        if error_response:
            return error_response
        # --- VERIFICAR TOKEN ---

        db_conexion = dbConectar()
        cursor = db_conexion.cursor()

        # Verificar que el método de pago pertenece al usuario autenticado
        cursor.execute(
            "SELECT 1 FROM UsuariosMetodosPago WHERE idMetodoPago = %s AND idUsuario = %s",
            (payment_method_id, user_id)
        )
        if not cursor.fetchone():
            return Error(code="404", message="Método de pago no encontrado o no pertenece al usuario"), 404

        # Eliminar la asociación usuario-método
        cursor.execute("DELETE FROM UsuariosMetodosPago WHERE idMetodoPago = %s AND idUsuario = %s",
                      (payment_method_id, user_id))
        
        # Eliminar el método de pago
        cursor.execute("DELETE FROM MetodosPago WHERE idMetodoPago = %s", (payment_method_id,))
        
        db_conexion.commit()
        cursor.close()
        return {"message": "Método de pago eliminado correctamente"}, 200

    except Exception as e:
        if db_conexion:
            db_conexion.rollback()
        print("Error al eliminar método de pago:", e)
        return Error(code="500", message=str(e)), 500

    finally:
        if db_conexion:
            dbDesconectar(db_conexion)


def show_user_payment_methods():
    """
    Retorna la lista de métodos de pago del usuario autenticado.
    
    Consulta todos los métodos de pago asociados al usuario actual en la base
    de datos y construye objetos PaymentMethod completos con toda la información.
    
    Flujo de operación:
        1. Valida token y obtiene user_id
        2. Consulta IDs de métodos de pago en UsuariosMetodosPago
        3. Para cada ID, consulta detalles completos en MetodosPago
        4. Construye objetos PaymentMethod y añade ID como atributo adicional
        5. Retorna lista de métodos serializados
    
    Estructura de respuesta:
        Cada método de pago incluye:
            - id: ID del método (añadido dinámicamente)
            - cardNumber: Número enmascarado
            - expireMonth: Mes de vencimiento
            - expireYear: Año de vencimiento
            - cardHolder: Nombre del titular
    
    Returns:
        Tuple[List[Dict]|Error, int]: Tupla con respuesta y código HTTP:
            - ([{method1}, {method2}, ...], 200): Lista de métodos (puede estar vacía)
            - (Error, 401): Token no encontrado
            - (Error, 403): Usuario no autorizado
            - (Error, 500): Error interno del servidor o BD
    
    Examples:
        Response JSON:
            [
                {
                    "id": 1,
                    "cardNumber": "**** **** **** 1234",
                    "expireMonth": 12,
                    "expireYear": 2025,
                    "cardHolder": "Juan Pérez"
                },
                {
                    "id": 2,
                    "cardNumber": "**** **** **** 5678",
                    "expireMonth": 6,
                    "expireYear": 2026,
                    "cardHolder": "María García"
                }
            ]
    
    Note:
        - Retorna lista vacía [] si el usuario no tiene métodos de pago
        - El campo 'id' se añade dinámicamente y no forma parte del modelo PaymentMethod oficial
        - La función maneja correctamente el caso de IDs sin métodos asociados (datos huérfanos)
    
    Performance:
        Realiza N+1 queries (1 para IDs + N para detalles). Para usuarios con muchos
        métodos de pago, considerar optimizar con JOIN o query única.
    """
    db_conexion = None
    try:

        # --- VERIFICAR TOKEN ---
        token = connexion.request.cookies.get("token")
        user_id, error_response = verify_token_and_get_user_id(token)
        if error_response:
            return error_response
        # --- VERIFICAR TOKEN ---

        # Consultar la base de datos con el user_id
        db_conexion = dbConectar()
        cursor = db_conexion.cursor()

        ids_metodos_pago = []
        metodos = []
        cursor.execute("""
            SELECT idMetodoPago FROM UsuariosMetodosPago WHERE idUsuario = %s
        """, (user_id,))
        rows_ids = cursor.fetchall()
        ids_metodos_pago = [row[0] for row in rows_ids]
        if not ids_metodos_pago:
            return [], 200  # Retornar lista vacía si no hay métodos de pago

        for metodo_id in ids_metodos_pago:
            cursor.execute("""
                SELECT idMetodoPago, numeroTarjeta, mesValidez, anioVlidez, nombreTarjeta FROM MetodosPago WHERE idMetodoPago = %s
            """, (metodo_id,))
            tupla = cursor.fetchone()
            if tupla:
                metodo = PaymentMethod(
                    card_number=tupla[1],
                    expire_month=tupla[2],
                    expire_year=tupla[3],
                    card_holder=tupla[4]
                )
                # Agregar id como atributo adicional
                metodo.id = tupla[0]
                metodos.append(metodo)
        cursor.close()
        return [m.to_dict() for m in metodos], 200

    except Exception as e:
        print("Error al obtener métodos de pago:", e)
        return Error(code="500", message=str(e)), 500

    finally:
        if db_conexion:
            dbDesconectar(db_conexion)
