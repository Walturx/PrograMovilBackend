# PrograMovilBackend\hotel_ya\apis\home.py

import traceback
from flask import Blueprint, jsonify, request
from main.models import Hotel, Room
from main.database import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

api = Blueprint('hotel_ya_apis_home', __name__)


@api.route('/apis/v1/home', methods=['GET'])
def get_home():
    """
    Endpoint para Home.

    GET /apis/v1/home
    Devuelve todos los hoteles activos.

    GET /apis/v1/home?q=paradise
    Devuelve hoteles filtrados por nombre, ciudad o país.
    """
    response = None
    status = 200
    session = Session()

    try:
        query = request.args.get('q', '').strip()

        hoteles_query = (
            session.query(Hotel)
            .options(
                joinedload(Hotel.location),
                joinedload(Hotel.amenities)
            )
            .filter(Hotel.is_active == True)
        )

        if query:
            hoteles_query = (
                hoteles_query
                .join(Hotel.location)
                .filter(
                    or_(
                        Hotel.name.ilike(f'%{query}%'),
                        Hotel.location.has(city=query),
                        Hotel.location.has(country=query)
                    )
                )
            )

        hotels = hoteles_query.all()

        hotels_list = []

        for hotel in hotels:
            available_rooms_count = (
                session.query(Room)
                .filter(
                    Room.hotel_id == hotel.id,
                    Room.is_available == True
                )
                .count()
            )

            hotels_list.append({
                'id': hotel.id,
                'name': hotel.name,
                'stars': hotel.stars,
                'rating': hotel.rating,
                'distance': '1.2 miles',
                'available_rooms': available_rooms_count,
                'cover_image_url': hotel.cover_image_url,
                'amenities': [
                    amenity.name for amenity in hotel.amenities[:2]
                ]
            })

        response = jsonify({
            'message': 'Lista de hoteles obtenida exitosamente',
            'data': hotels_list,
            'success': True,
            'error': None,
            'query': query
        })

    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error',
            'error': str(e),
            'data': None,
            'success': False
        })
        status = 500

    finally:
        session.close()

    return response, status