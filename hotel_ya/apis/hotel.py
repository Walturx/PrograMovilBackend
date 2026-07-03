# Backend/HotelYa/hotel_ya/apis/hotel.py

# ==============================================================================
# ARCHIVO: hotel_ya/apis/hotel.py
# PROPÓSITO: Este módulo define los endpoints de la API de Flask para la pantalla
#            de detalles del hotel (Hotel Details Screen) en la app de Flutter.
#            Se encarga de recopilar de manera centralizada la ficha de un hotel
#            específico utilizando su identificador único (id_hotel), incluyendo 
#            su inventario de habitaciones disponibles, catálogo de servicios 
#            asociados y la lista de amenidades destacadas. Actúa como capa de
#            adaptación para transformar los modelos relacionales de la BD en un
#            árbol JSON anidado de alto rendimiento para el Front-End.
# ==============================================================================

import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from main.database import Session
from hotel_ya.models import Hotel, Room, Review, Service
from sqlalchemy.orm import joinedload
from sqlalchemy import func

# Creación del Blueprint para registrar el módulo de gestión de hoteles en Flask
api = Blueprint('hotel_ya_apis_hotels', __name__)

@api.route('/apis/v1/hotels/<string:hotel_id>', methods=['GET'])
def get_hotel_details(hotel_id):
    """
    Endpoint para Detalle de Hotel.

    GET /apis/v1/hotels/<hotel_id>
    Trae los detalles completos de un hotel en específico, sus habitaciones activas,
    servicios adicionales y amenidades filtrados por el ID del hotel.

    ---
    Parámetros de Ruta (Path Parameters):
        - hotel_id (string): El identificador único del hotel (UML: id_hotel).

    Estructura del JSON de Retorno con Éxito (Status 200):
        {
            "success": true,
            "message": "Detalle del hotel obtenido correctamente",
            "error": null,
            "data": {
                "id": "string",
                "name": "string",
                "description": "string",
                "stars": int,
                "rating": float,
                "cover_image_url": "string",
                "rooms": [
                    {
                        "id": "string",
                        "room_number": "string",
                        "floor": int,
                        "is_available": bool,
                        "image_url": "string",
                        "room_type": {
                            "id": "string",
                            "name": "string",
                            "base_price": float,
                            "capacity": int
                        }
                    }
                ],
                "services": [ ... ],
                "amenities": [ ... ]
            }
        }
    """
    session = Session()
    try:
        # 💡 Sincronización UML: Buscamos el hotel usando 'id_hotel' conforme a la tabla física
        hotel = session.query(Hotel).filter(Hotel.id_hotel == hotel_id).first()
        
        if not hotel:
            return jsonify({
                'message': f'No se encontró el hotel con ID {hotel_id}',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404
        
        # 💡 Optimización N+1: Cargamos las habitaciones y sus tipos correspondientes en un solo viaje
        rooms = (
            session.query(Room)
            .options(joinedload(Room.room_type))
            .filter(Room.hotel_id == hotel.id_hotel)
            .all()
        )

        # Buscamos los servicios adicionales vinculados a este hotel en la BD
        services = (
            session.query(Service)
            .filter(Service.hotel_id == hotel.id_hotel)
            .all()
        )

        # Cálculo dinámico en tiempo real del rating promedio del hotel basado en la tabla reviews
        rating_avg = (
            session.query(func.avg(Review.rating))
            .filter(Review.hotel_id == hotel.id_hotel)
            .scalar()
        )
        rating_final = round(float(rating_avg), 1) if rating_avg else 4.5

        # Mapeo limpio de amenidades asociadas al formato plano que requiere Flutter
        amenities_list = []
        if hasattr(hotel, 'amenities') and hotel.amenities:
            for amenity in hotel.amenities:
                amenities_list.append({
                    'id': amenity.id_amenity,
                    'name': amenity.name,
                    'icon': amenity.icon if amenity.icon else 'help_outline',
                    'category': amenity.category if amenity.category else 'General'
                })

        # Construcción del árbol JSON optimizado para la deserialización en Dart
        data = {
            'id': hotel.id_hotel,  # Mapeado de id_hotel (BD) a id (Flutter) para simplificar modelos
            'name': hotel.name,
            'description': hotel.description if hotel.description else '',
            'stars': hotel.stars,
            'rating': rating_final,
            'cover_image_url': hotel.cover_image_url,
            
            # Sub-lista mapeada de habitaciones
            'rooms': [
                {
                    'id': room.id_room,
                    'room_number': room.room_number,
                    'floor': room.floor if room.floor else 1,
                    'is_available': bool(room.is_available),
                    'image_url': room.image_url if room.image_url else '',
                    'room_type': {
                        'id': room.room_type.id_room_type if room.room_type else None,
                        'name': room.room_type.name if room.room_type else 'Estándar',
                        'base_price': float(room.room_type.base_price) if room.room_type else 0.0,
                        'capacity': room.room_type.capacity if room.room_type else 2
                    }
                }
                for room in rooms
            ],
            
            # Sub-lista de servicios adicionales disponibles en este complejo hotelero
            'services': [
                {
                    'id': service.id_service,      # Mapeo estricto del UML id_service -> id hacia Flutter
                    'name': service.name,
                    'price': float(service.price),
                    'description': service.description if service.description else ''
                }
                for service in services
            ],
            'amenities': amenities_list
        }

        # Envío de la respuesta HTTP 200 con la estructura unificada
        return jsonify({
            'message': 'Detalle del hotel obtenido correctamente',
            'data': data,
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        # Volcado de la traza completa en el servidor backend en caso de fallo crítico
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error al obtener el detalle del hotel',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500

    finally:
        # Cierre definitivo de la sesión de SQLAlchemy para evitar fugas en el pool de conexiones
        session.close()

@api.route('/apis/v1/reviews', methods = ['POST'])
def send_review():
    response = None
    status = 200
    session = Session()

    data = request.get_json()

    if not data or 'hotel_id' not in data or 'user_id' not in data:
        return jsonify({'success': False, 'message': 'Error al enviar la reseña'}), 400

    try:
        # La columna real del modelo es 'rating' (aceptamos 'rating' o el legacy 'star')
        rating = data.get('rating', data.get('star'))
        comment = data.get('comment')
        hotel_id = data.get('hotel_id')
        user_id = data.get('user_id')

        # Generamos la PK id_review (el modelo no tiene default para la clave primaria)
        review_id = f"rev_{int(datetime.utcnow().timestamp())}"

        new_review = Review(
            id_review=review_id,
            rating=rating,
            comment=comment,
            hotel_id=hotel_id,
            user_id=user_id
        )
        session.add(new_review)
        session.commit()

        response = jsonify({
            'message': 'Reseña enviada correctamente',
            'data': {
                'id': new_review.id_review,
                'rating': new_review.rating,
                'comment': new_review.comment,
                'hotel_id': new_review.hotel_id,
                'user_id': new_review.user_id,
                'created_at': new_review.created_at.isoformat() if new_review.created_at else None
            },
            'success': True,
            'error': None
        })
        status = 201
        
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error al enviar la reseña',
            'data': None,
            'success': False,
            'error': str(e)
        })
        status = 500
    finally:
        session.close()
    return response, status

@api.route('/apis/v1/reviews',methods = ["GET"])
def get_reviews():
    response = None
    status = 200
    session = Session()
    try:
        hotel_id = request.args.get('hotel_id')
        reviews = session.query(Review).options(
            joinedload(Review.user)
        ).filter(Review.hotel_id == hotel_id).all()

        response = jsonify({
            'message': 'Reseñas obtenidas correctamente',
            'data': [
                {
                    'id': review.id_review,
                    'rating': review.rating,
                    'comment': review.comment,
                    'hotel_id': review.hotel_id,
                    'user_id': review.user_id,
                    'user': {
                        'id': review.user.id_user,
                        'name': review.user.name,
                        'email': review.user.email,
                    } if review.user else None
                }
                for review in reviews
            ],
            'success': True,
            'error': None
        })
        status = 200

    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Ocurrió un error al enviar la reseña',
            'data': None,
            'success': False,
            'error': str(e)
        })
        status = 500
    finally:
        session.close()
    return response, status