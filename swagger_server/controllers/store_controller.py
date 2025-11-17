"""
Controlador de Tienda (Storefront).

Este módulo gestiona la visualización del catálogo de productos disponibles en
la tienda de OverSounds. Integra datos del microservicio de Temas y Autores (TyA)
para mostrar canciones, álbumes y merchandising en el escaparate de la tienda.

Características:
    - Consulta de catálogo completo de productos
    - Integración con microservicio TyA para datos actualizados
    - Mapeo y transformación de datos entre microservicios
    - Formato unificado de productos (Product) independiente del origen
    - Manejo resiliente de errores de comunicación

Arquitectura:
    Este controlador actúa como intermediario entre:
        - Frontend (cliente) que consume el endpoint /store
        - Microservicio TyA que proporciona los datos de productos
    
    Beneficios del patrón:
        - Desacoplamiento entre frontend y TyA
        - Transformación de datos centralizada
        - Caché potencial (no implementado)
        - Agregación de múltiples fuentes de datos

Dependencias:
    - Microservicio TyA (Temas y Autores): Fuente de datos de productos
        Endpoints utilizados:
            - GET /song/filter: Filtra canciones (sin parámetros devuelve todas)
            - GET /album/filter: Filtra álbumes (sin parámetros devuelve todos)
            - GET /merch/filter: Filtra merchandising (sin parámetros devuelve todos)
            - GET /song/list?ids=...: Obtiene detalles completos de canciones por IDs
            - GET /album/list?ids=...: Obtiene detalles completos de álbumes por IDs
            - GET /merch/list?ids=...: Obtiene detalles completos de merch por IDs

Modelo de datos:
    Transforma datos de TyA al modelo Product de TPP, que incluye:
        - Información básica: nombre, precio, descripción
        - Metadatos: artista, colaboradores, género, fecha de lanzamiento
        - Contenido multimedia: portada (cover en base64)
        - Información específica por tipo (duración para canciones, lista de canciones para álbumes)

Performance:
    - Realiza 3 peticiones HTTP síncronas al microservicio TyA
    - Considera implementar caché para reducir latencia y carga en TyA
    - Timeout configurado a 5 segundos por petición
    - Implementa paginación para optimizar transferencia de datos
"""

import requests
from swagger_server.models.error import Error
from swagger_server.models.product import Product
from swagger_server.controllers.config import TYA_SERVICE_URL

def show_storefront_products(page=1, limit=20):
    """
    Obtiene y retorna el catálogo paginado de productos de la tienda.
    
    Consulta el microservicio de Temas y Autores (TyA) para obtener todos los
    productos disponibles (canciones, álbumes y merchandising) y los transforma
    al formato Product esperado por el frontend, aplicando paginación a los resultados.
    
    Args:
        page (int, optional): Número de página a retornar (comienza en 1). Default: 1.
        limit (int, optional): Cantidad de productos por página (1-100). Default: 20.
    
    Flujo de operación:
        1. Realiza 3 peticiones HTTP al microservicio TyA usando endpoints filter:
           - GET /song/filter: Obtiene IDs de todas las canciones
           - GET /album/filter: Obtiene IDs de todos los álbumes
           - GET /merch/filter: Obtiene IDs de todo el merchandising
        2. Para cada tipo, obtiene detalles completos usando endpoints list:
           - GET /song/list?ids=...: Detalles de canciones
           - GET /album/list?ids=...: Detalles de álbumes
           - GET /merch/list?ids=...: Detalles de merchandising
        3. Mapea cada tipo de producto al modelo Product
        4. Combina todos los productos en una lista única
        5. Aplica paginación sobre los resultados
        6. Serializa y retorna la lista paginada con metadata
    
    Mapeo de datos:
        Canciones:
            - songId, albumId: Directos desde TyA
            - title → name
            - artistId → artist (convertido a string)
            - releaseDate: Formateado con zona horaria UTC
            - collaborators → colaborators (convertido a lista de strings)
            - genres[0] → genre (primer género, convertido a string)
            - Campos específicos: duration
        
        Álbumes:
            - albumId: Directo desde TyA
            - title → name
            - songs → song_list (convertido a lista de strings)
            - genre = "Merch" (hardcoded para merchandising)
        
        Merchandising:
            - merchId: Directo desde TyA
            - genre fijado a "Merch"
            - Sin duración ni lista de canciones
    
    Manejo de errores:
        - Si falla la conexión con TyA, retorna listas vacías para ese tipo
        - Errores de conexión se registran en consola
        - La función continúa con los tipos disponibles
        - Errores generales retornan objeto Error con código 500
    
    Returns:
        Dict|Error: Objeto con datos paginados y metadata, o Error en caso de fallo crítico.
            Éxito: {
                "data": [Product, ...],  # Lista de productos de la página actual
                "pagination": {
                    "page": int,         # Página actual
                    "limit": int,        # Productos por página
                    "total": int,        # Total de productos disponibles
                    "totalPages": int    # Total de páginas
                }
            }
            Error: Objeto Error con código 500 y mensaje descriptivo
    
    Examples:
        Request:
            GET /store?page=2&limit=10
        
        Response JSON:
            {
                "data": [
                    {
                        "songId": 42,
                        "albumId": 5,
                        "merchId": 0,
                        "name": "Bohemian Rhapsody",
                        "artist": "12",
                        "price": 1.99,
                        "duration": 354,
                        "genre": "3",
                        "cover": "data:image/png;base64,...",
                        ...
                    },
                    {
                        "albumId": 10,
                        "name": "Dark Side of the Moon",
                        "songList": ["1", "2", "3"],
                        ...
                    }
                ],
                "pagination": {
                    "page": 2,
                    "limit": 10,
                    "total": 150,
                    "totalPages": 15
                }
            }
    
    Paginación:
        - Si page < 1, se ajusta automáticamente a 1
        - Si page > totalPages, se ajusta a la última página disponible
        - Si limit excede el máximo (100), el servidor puede rechazarlo
        - Lista vacía si no hay productos en el rango solicitado
    
    Performance considerations:
        - 6 peticiones HTTP síncronas (3 para IDs + 3 para detalles)
        - Timeout de 5 segundos por petición
        - No implementa caché (cada request consulta TyA)
        - Paginación se aplica en memoria después de obtener todos los productos
        - Implementación actual más eficiente que consultas individuales
        - Considera implementar:
            * Peticiones asíncronas con asyncio
            * Caché con TTL configurable
            * Paginación a nivel de TyA para reducir transferencia
            * Batch único si TyA implementa endpoint combinado
    
    Data transformation:
        - IDs numéricos se convierten a strings para consistencia
        - Fechas se formatean con zona horaria UTC explícita
        - Valores por defecto (0, [], "") para campos opcionales
        - Listas de colaboradores/canciones se convierten a strings
    
    Note:
        - Este controlador NO utiliza base de datos
        - Todos los datos provienen del microservicio TyA
        - Los géneros se manejan como el primer elemento de la lista de TyA
    """
    try:
        productos = []

        # --- Obtener datos del microservicio Temas y Autores ---
        try:
            # PASO 1: Obtener IDs usando endpoints /filter (sin parámetros = todos)
            # -----------------------------------------------------------------------
            # Los endpoints /song/filter, /album/filter y /merch/filter retornan
            # listas de objetos con solo los IDs cuando se llaman sin parámetros.
            # Esto es más eficiente que obtener objetos completos inicialmente.
            # Formato de respuesta: [{"songId": 1}, {"songId": 2}, ...]
            
            song_ids_response = requests.get(
                f"{TYA_SERVICE_URL}/song/filter",
                timeout=5.0,
                headers={"Accept": "application/json"}
            )
            album_ids_response = requests.get(
                f"{TYA_SERVICE_URL}/album/filter",
                timeout=5.0,
                headers={"Accept": "application/json"}
            )
            merch_ids_response = requests.get(
                f"{TYA_SERVICE_URL}/merch/filter",
                timeout=5.0,
                headers={"Accept": "application/json"}
            )
            
            # Extraer solo los IDs numéricos de los objetos de respuesta
            # Validación: solo incluye items que tengan el campo ID correspondiente
            song_ids = [item.get("songId") for item in song_ids_response.json() if item.get("songId")] if song_ids_response.ok else []
            album_ids = [item.get("albumId") for item in album_ids_response.json() if item.get("albumId")] if album_ids_response.ok else []
            merch_ids = [item.get("merchId") for item in merch_ids_response.json() if item.get("merchId")] if merch_ids_response.ok else []
            
            # PASO 2: Obtener detalles completos usando endpoints /list
            # ----------------------------------------------------------
            # Los endpoints /song/list, /album/list y /merch/list aceptan múltiples
            # IDs en formato comma-separated (ej: "1,2,3,5,8") y retornan los objetos
            # completos con toda la información (title, price, cover, etc.).
            # Esto permite hacer batch requests en lugar de N peticiones individuales.
            canciones = []
            albumes = []
            merch = []
            
            # Solo hacer petición si existen IDs (optimización)
            if song_ids:
                ids_str = ",".join(map(str, song_ids))  # Convertir lista a "1,2,3,..."
                response = requests.get(
                    f"{TYA_SERVICE_URL}/song/list?ids={ids_str}",
                    timeout=5.0,
                    headers={"Accept": "application/json"}
                )
                if response.ok:
                    canciones = response.json()
            
            if album_ids:
                ids_str = ",".join(map(str, album_ids))
                response = requests.get(
                    f"{TYA_SERVICE_URL}/album/list?ids={ids_str}",
                    timeout=5.0,
                    headers={"Accept": "application/json"}
                )
                if response.ok:
                    albumes = response.json()
            
            if merch_ids:
                ids_str = ",".join(map(str, merch_ids))
                response = requests.get(
                    f"{TYA_SERVICE_URL}/merch/list?ids={ids_str}",
                    timeout=5.0,
                    headers={"Accept": "application/json"}
                )
                if response.ok:
                    merch = response.json()
                    
        except requests.RequestException as e:
            print(f"Error al conectar con Temas y Autores: {e}")
            canciones, albumes, merch = [], [], []
        except Exception as e:
            print(f"Error inesperado al obtener datos de TyA: {e}")
            canciones, albumes, merch = [], [], []

        # --- Mapear / Enmascarar canciones ---
        for c in canciones:
            productos.append(Product(
                song_id=c.get("songId"),
                name=c.get("title"),
                artist=c.get("artistId"),
                release_date=f"{c.get('releaseDate')}T00:00:00Z",
                album_id=c.get("albumId"),
                description=c.get("description"),
                song_list=[],
                merch_id=0,
                duration=c.get("duration"),
                cover=c.get("cover"),
                price=c.get("price"),
                genre=c.get("genres", [0])[0] if c.get("genres") else 0,
                colaborators=c.get("collaborators", [])
            ))

        # --- Mapear álbumes ---
        for a in albumes:
            productos.append(Product(
                song_id=0,
                name=a.get("title"),
                artist=a.get("artistId"),
                release_date=f"{a.get('releaseDate')}T00:00:00Z",
                album_id=a.get("albumId"),
                description=a.get("description"),
                song_list=a.get("songs", []),
                merch_id=0,
                duration=0,
                cover=a.get("cover"),
                price=a.get("price"),
                genre=a.get("genres", [0])[0] if a.get("genres") else 0,
                colaborators=a.get("collaborators", [])
            ))

        # --- Mapear merch ---
        for m in merch:
            productos.append(Product(
                song_id=0,
                name=m.get("title"),
                artist=m.get("artistId"),
                release_date=f"{m.get('releaseDate')}T00:00:00Z",
                album_id=0,
                description=m.get("description"),
                song_list=[],
                merch_id=m.get("merchId"),
                duration=0,
                cover=m.get("cover"),
                price=m.get("price"),
                genre=None,  # Merch no tiene género en TyA
                colaborators=m.get("collaborators", [])
            ))

        # --- Aplicar paginación ---
        # Validar y ajustar parámetros de paginación
        if page is None or page < 1:
            page = 1
        if limit is None or limit < 1:
            limit = 20
        if limit > 100:
            limit = 100
        
        # Calcular metadata de paginación
        total_productos = len(productos)
        total_pages = (total_productos + limit - 1) // limit if total_productos > 0 else 1
        
        # Ajustar página si excede el total
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        # Calcular índices de slice para la página solicitada
        start_index = (page - 1) * limit
        end_index = start_index + limit
        
        # Aplicar paginación sobre la lista completa
        productos_paginados = productos[start_index:end_index]
        
        # --- Retornar respuesta con datos paginados y metadata ---
        return {
            "data": [p.to_dict() for p in productos_paginados],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_productos,
                "totalPages": total_pages
            }
        }

    except Exception as e:
        print(f"Error general al obtener los productos: {e}")
        return Error(code="500", message=str(e)), 500
