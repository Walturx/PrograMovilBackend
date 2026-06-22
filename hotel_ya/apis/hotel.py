# hotel_ya\apis\hotel.py
import traceback
from flask import Blueprint, jsonify, request
from main.database import Session
from main.models import Hotel, Room, Amenity
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

api = Blueprint('hotel_ya_apis_hotels', __name__)

@api.route('/apis/v1/hotels/<string:hotel_id>', methods=['GET'])
def get_hotel_details(hotel_id):
    """
    Trae los detalles completos del hotel y las habitaciones disponibles
    """
    response = None
    status = 200
    session = Session()
    try:
        hotel = session.query(Hotel).options(
            joinedload(Hotel.amenities),
            joinedload(Hotel.reviews),
            joinedload(Hotel.services)
        ).filter(Hotel.id == hotel_id).first()
        
        if not hotel:
            return jsonify({
                'message': f'No se encontró el hotel con ID {hotel_id}',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404
        
        rooms = session.query(Room).options(joinedload(Room.room_type)).filter(Room.hotel_id == hotel_id).all()

        data = {
            'id': hotel.id,
            'name': hotel.name,
            'description': hotel.description,
            'stars': hotel.stars,
            'phone': hotel.phone,
            'email': hotel.email,
            'cover_image_url': hotel.cover_image_url,
            'is_active': hotel.is_active,

            'location': {
                'id': hotel.location.id if hotel.location else None,
                'country': hotel.location.country if hotel.location else None,
                'city': hotel.location.city if hotel.location else None,
                'state': hotel.location.state if hotel.location else None,
            },

            'rooms': [
                {
                    'id': room.id,
                    'room_number': room.room_number,
                    'floor': room.floor,
                    'is_available': room.is_available,
                    'image_url': room.image_url,
                    'room_type': {
                        'id': room.room_type.id if room.room_type else None,
                        'base_price': room.room_type.base_price if room.room_type else None,
                        'capacity': room.room_type.capacity if room.room_type else None,
                    }
                }
                for room in rooms
            ],
            'amenities': [
                {
                    'name': amenity.name,
                    'icon': amenity.icon,
                    'category': amenity.category
                }
                for amenity in hotel.amenities
            ]
        }

        response = jsonify({
            'message': 'Detalle del hotel obtenido correctamente',
            'data': data,
            'success': True,
            'error': None
        })
        status = 200

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