# hotel_ya\apis\hotel.py
import traceback
from flask import Blueprint, jsonify, request
from main.database import Session
from main.models import Hotel, Room
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

api = Blueprint('hotel_ya_apis_hotels', __name__)

@api.route('/apis/v1/hotels', methods=['GET'])
def fetch_all_hotels():
    """
    Endpoint para la pantalla '/home'.
    Trae la lista de todos los hoteles activos junto con su ciudad.
    """
    response = None
    status = 200
    session = Session()
    try:
        # Usamos joinedload para optimizar la relación con Location en una sola consulta SQL
        hotels = (
            session.query(Hotel)
            .options(joinedload(Hotel.location))
            .filter(Hotel.is_active == True)
            .all()
        )
        
        # Mapeamos la lista de objetos usando el to_dict() limpio sincronizado con Flutter
        hotels_list = [h.to_dict() for h in hotels]

        response = jsonify({
            'message': 'Lista de hoteles disponibles obtenida exitosamente',
            'data': hotels_list,
            'success': True,
            'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error al listar los hoteles',
            'data': None,
            'success': False,
            'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/hotels/search', methods=['GET'])
def search_hotels():
    """
    Endpoint para la pantalla '/search'.
    Permite filtrar dinámicamente por término de búsqueda (nombre, ciudad o país).
    """
    response = None
    status = 200
    query = request.args.get('query', '').strip()
    
    session = Session()
    try:
        # Generamos la consulta uniendo la tabla de ubicaciones para realizar filtros inteligentes
        hotels = (
            session.query(Hotel)
            .join(Hotel.location)
            .filter(
                Hotel.is_active == True,
                or_(
                    Hotel.name.ilike(f"%{query}%"),
                    Hotel.location.city.ilike(f"%{query}%"),
                    Hotel.location.country.ilike(f"%{query}%")
                )
            )
            .all()
        )
        
        hotels_list = [h.to_dict() for h in hotels]

        response = jsonify({
            'message': f"Resultados de búsqueda para: '{query}'",
            'data': hotels_list,
            'success': True,
            'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error durante la búsqueda de hoteles',
            'data': None,
            'success': False,
            'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/hotels/<string:hotel_id>', methods=['GET'])
def get_hotel_details(hotel_id):
    """
    Endpoint para la pantalla '/hotel'.
    Trae la información detallada y extendida de un único hotel.
    """
    response = None
    status = 200
    session = Session()
    try:
        hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        
        if not hotel:
            return jsonify({
                'message': f'No se encontró el hotel con ID {hotel_id}',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404

        response = jsonify({
            'message': 'Detalle del hotel obtenido correctamente',
            'data': hotel.to_dict(),
            'success': True,
            'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error al obtener el detalle del hotel',
            'data': None,
            'success': False,
            'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/hotels/<string:hotel_id>/amenities', methods=['GET'])
def get_hotel_amenities(hotel_id):
    """
    Endpoint complementario para la pantalla '/hotel'.
    Lista los servicios y comodidades (Amenities) que ofrece el establecimiento.
    """
    response = None
    status = 200
    session = Session()
    try:
        hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
        
        if not hotel:
            return jsonify({
                'message': f'No se encontró el hotel con ID {hotel_id}',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404

        amenities_list = [
            {'id': a.id, 'name': a.name, 'icon': a.icon, 'category': a.category} for a in hotel.amenities
        ]

        response = jsonify({
            'message': 'Comodidades del hotel obtenidas',
            'data': amenities_list,
            'success': True,
            'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error al obtener las comodidades',
            'data': None,
            'success': False,
            'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/hotels/<string:hotel_id>/rooms', methods=['GET'])
def get_hotel_rooms(hotel_id):
    """
    Endpoint para la pantalla '/rooms'.
    Lista todas las habitaciones que se encuentran disponibles en este hotel.
    """
    response = None
    status = 200
    session = Session()
    try:
        # Pre-cargamos la relación room_type para evitar consultas adicionales en bucle
        rooms = (
            session.query(Room)
            .options(joinedload(Room.room_type))
            .filter(Room.hotel_id == hotel_id, Room.is_available == True)
            .all()
        )
        
        rooms_list = [r.to_dict() for r in rooms]

        response = jsonify({
            'message': 'Habitaciones disponibles obtenidas correctamente',
            'data': rooms_list,
            'success': True,
            'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error al listar las habitaciones',
            'data': None,
            'success': False,
            'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status