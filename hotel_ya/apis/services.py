# hotel_ya\apis\services.py
import traceback
from datetime import datetime
import uuid  # Usamos uuid para generar IDs alfanuméricos únicos consistentes con strings
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from main.database import Session
from sqlalchemy.orm import joinedload
from main.models import Service, ReservationService, Reservation

api = Blueprint('hotel_ya_apis_services', __name__)

@api.route('/apis/v1/services', methods=['GET'])
def get_available_services():
    """
    Lista todos los servicios adicionales disponibles en el hotel (Room service, Spa, etc.)
    """
    session = Session()
    try:
        # Nota: En tus modelos la tabla 'services' no tiene 'is_available', 
        # así que listamos todos los servicios asociados.
        services = session.query(Service).all()
        return jsonify({
            'message': 'Catálogo de servicios adicionales obtenido',
            'data': [s.to_dict() for s in services],
            'success': True, 'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al obtener el catálogo de servicios',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/services/request', methods=['POST'])
@jwt_required()
def request_room_service():
    """
    Registra de forma transaccional el cargo de un servicio extra a una reserva activa.
    Suma de inmediato el costo al total de la reserva.
    """
    data = request.get_json()

    if not data or 'reservationId' not in data or 'serviceId' not in data:
        return jsonify({
            'message': 'Los parámetros reservationId y serviceId son obligatorios',
            'data': None, 'success': False, 'error': 'Bad Request'
        }), 400

    reservation_id = data['reservationId']
    service_id = data['serviceId']
    quantity = int(data.get('quantity', 1))

    session = Session()
    try:
        # 1. Validar la existencia de la reserva
        reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            return jsonify({
                'message': 'La reserva provista no existe',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        # 2. Validar existencia del servicio (Usa 'Service' en lugar de 'AdditionalService')
        service = session.query(Service).filter(Service.id == service_id).first()
        if not service:
            return jsonify({
                'message': 'El servicio solicitado no existe',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        # Calcular costo acumulado
        subtotal_charge = float(service.price * quantity)

        # 3. Insertar el registro en la tabla puente (reservation_services) 
        # Adaptado a las columnas exactas de tus modelos: id, reservation_id, service_id, quantity, subtotal
        res_service = ReservationService(
            id=str(uuid.uuid4())[:8], # Genera un ID corto alfanumérico para cumplir con el tipo String
            reservation_id=reservation.id,
            service_id=service.id,
            quantity=quantity,
            subtotal=subtotal_charge
        )
        session.add(res_service)

        # 4. Actualizar el total de la reserva agregando este cargo dinámicamente
        if reservation.total_price is None:
            reservation.total_price = 0.0
        reservation.total_price += subtotal_charge

        session.commit()

        return jsonify({
            'message': f'Servicio de {service.name} solicitado con éxito al cuarto',
            'data': res_service.to_dict(),
            'success': True, 'error': None
        }), 201

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Error de consistencia al procesar la solicitud del servicio',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations/<string:reservation_id>/services', methods=['GET'])
@jwt_required()
def get_reservation_services(reservation_id):
    """
    Lista todos los cargos extras y room-service asociados a una estadía específica.
    """
    session = Session()
    try:
        # Usamos joinedload mapeando la relación correcta 'service' definida en ReservationService
        items = (
            session.query(ReservationService)
            .options(joinedload(ReservationService.service))
            .filter(ReservationService.reservation_id == reservation_id)
            .all()
        )
        
        return jsonify({
            'message': 'Consumos extras de la habitación obtenidos',
            'data': [i.to_dict() for i in items],
            'success': True, 'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al obtener los consumos extras',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()