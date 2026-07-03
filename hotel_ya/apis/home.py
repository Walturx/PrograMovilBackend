# ==============================================================================
# ARCHIVO: hotel_ya/apis/home.py
# PROPÓSITO: Este módulo define los endpoints de la API de Flask correspondientes
#            a la pantalla principal o de inicio (Home) de la aplicación móvil.
#            Su objetivo es centralizar la búsqueda, filtrado y catalogación de
#            los hoteles disponibles dentro del ecosistema "Hotel Ya". Además,
#            actúa como un adaptador de datos de backend, transformando los modelos
#            del UML/Base de Datos en estructuras JSON estándar de alto rendimiento
#            compatibles con el patrón de consumo de la aplicación móvil Flutter.
# ==============================================================================

import traceback
from flask import Blueprint, jsonify, request
from hotel_ya.models import Hotel, Room, Location, Review
from main.database import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func

# Creación del Blueprint para registrar el módulo en la aplicación Flask central
api = Blueprint('hotel_ya_apis_home', __name__)

@api.route('/apis/v1/home', methods=['GET'])
def get_home():
    """
    Endpoint para Home.

    GET /apis/v1/home
    Devuelve todos los hoteles activos mapeados detalladamente al formato de Flutter.

    GET /apis/v1/home?q=paradise
    Devuelve hoteles filtrados por nombre, ciudad o país mediante búsquedas relacionales.

    ---
    Parámetros de Consulta (Query Parameters):
        - q (string): Cadena opcional para filtrar los hoteles.
    """
    session = Session()

    try:
        query = request.args.get('q', '').strip()

        # Configuración inicial de la consulta cargando de forma ansiosa (Eager Loading) las relaciones
        hoteles_query = (
            session.query(Hotel)
            .options(
                joinedload(Hotel.location),
                joinedload(Hotel.amenities)
            )
            .filter(Hotel.is_active == True)
        )

        # Si el usuario ingresa un texto en la barra de búsqueda (SearchPage)
        if query:
            hoteles_query = (
                hoteles_query
                .join(Hotel.location)
                .filter(
                    or_(
                        Hotel.name.ilike(f'%{query}%'),
                        Location.city.ilike(f'%{query}%'),
                        Location.country.ilike(f'%{query}%')
                    )
                )
            )

        hotels = hoteles_query.all()
        hotels_list = []

        for hotel in hotels:
            # 💡 CORRECCIÓN CRÍTICA: Se cambió 'hotel.id' por 'hotel.id_hotel' de acuerdo al esquema SQL
            available_rooms_count = (
                session.query(Room)
                .filter(
                    Room.hotel_id == hotel.id_hotel,
                    Room.is_available == True
                )
                .count()
            )

            # Cálculo en tiempo real del promedio de calificación de reseñas para este hotel
            rating_avg = (
                session.query(func.avg(Review.rating))
                .filter(Review.hotel_id == hotel.id_hotel)
                .scalar()
            )
            rating_final = round(float(rating_avg), 1) if rating_avg else 4.5

            # Extracción limpia de los nombres de las amenidades asociadas para Flutter tags
            amenities_nombres = [amenity.name for amenity in hotel.amenities[:2]]

            # Construcción de la entidad de respuesta adaptada a Dart (HotelModel.fromJson)
            hotels_list.append({
                'id': hotel.id_hotel,                # 💡 CORRECCIÓN CRÍTICA: Se expone 'id_hotel' bajo la clave 'id' hacia Flutter
                'name': hotel.name,
                'stars': hotel.stars,
                'rating': rating_final,             # Inyectado dinámicamente sin romper la tabla original
                'distance': '1.2 miles',            # Simulado temporalmente para la interfaz de geolocalización
                'available_rooms': available_rooms_count,
                'cover_image_url': hotel.cover_image_url,
                'tags': amenities_nombres           # Lista estructurada de strings consumida directamente en Flutter
            })

        # Respuesta exitosa estructurada en base al estándar unificado del proyecto móvil
        return jsonify({
            'message': 'Lista de hoteles obtenida exitosamente',
            'data': hotels_list,
            'success': True,
            'error': None,
            'query': query if query else None
        }), 200

    except Exception as e:
        # Impresión estricta del traceback completo en la terminal del backend para propósitos de depuración rápida
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error interno al compilar el Home',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500

    finally:
        # Bloque de seguridad crítico: Cerramos la sesión de base de datos para liberar recursos en el pool de conexiones
        session.close()