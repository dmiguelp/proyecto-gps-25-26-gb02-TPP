import psycopg2 as DB
from psycopg2.extensions import connection
import os

def dbConectar() -> connection:
    ip = os.getenv('DB_HOST', '10.1.1.1')
    puerto = os.getenv('DB_PORT', 5432)
    basedatos = os.getenv('DB_NAME', 'tpp')

    usuario = os.getenv('DB_USER', 'tpp_admin')
    contrasena = os.getenv('DB_PWD', '12345')

    print("---dbConectar---")
    print("---Conectando a Postgresql---")

    try:
        conexion = DB.connect(user=usuario, password=contrasena, host=ip, port=puerto, database=basedatos)
        conexion.autocommit = False
        print("Conexión realizada a la base de datos", conexion)
        return conexion
    except DB.DatabaseError as error:
        print("Error en la conexión")
        print(error)
        return None

def dbDesconectar(conexion):
    print("---dbDesconectar---")
    try:
        conexion.commit()
        conexion.close()
        print("Desconexión realizada correctamente")
        return True
    except DB.DatabaseError as error:
        print("Error en la desconexión")
        print(error)
        return False