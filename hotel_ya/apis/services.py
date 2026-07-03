# ==============================================================================
# ARCHIVO: hotel_ya/apis/services.py
# PROPÓSITO: Este módulo define los endpoints de la API de Flask relacionados con
#            el catálogo de servicios adicionales del hotel y el registro de 
#            consumos extras vinculados a una habitación o reserva en tiempo real.
#            Garantiza que la aplicación en Flutter pueda listar amenidades de pago
#            y cargar cargos adicionales a la cuenta del huésped de forma segura.
# ==============================================================================

import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from main.database import Session
from hotel_ya.models import Service, ReservationService, Reservation
from sqlalchemy.orm import joinedload

# Creación del Blueprint para registrar el módulo de servicios adicionales en Flask
api = Blueprint('hotel_ya_apis_services', __name__)

@api.route('/apis/v1/services', methods=['GET'])
def get_available_services():
    """
    Endpoint para el Catálogo Global de Servicios.

    GET /apis/v1/services
    Lista todos los servicios adicionales disponibles en el ecosistema hotelero 
    (Room service, Spa, Lavandería, etc.) mapeados al formato que Flutter requiere.

    ---
    Estructura del JSON de Retorno con Éxito (Status 200):
        {
            "success": true,
            "message": "Catálogo de servicios adicionales obtenido con éxito",
            "error": null,
            "data": [
                {
                    "id": "string (UML: id_service)",
                    "hotel_id": "string",
                    "name": "string",
                    "price": float,
                    "description": "string"
                }
            ]
        }
    """
    session = Session()
    try:
        # Recuperamos la lista completa de servicios del sistema
        services = session.query(Service).all()
        
        services_list = []
        for s in services:
            # Adaptador Front-End: Mapeamos id_service a 'id' para la consistencia con Dart
            services_list.append({
                'id': s.id_service,
                'hotel_id': s.hotel_id,
                'name': s.name,
                'price': float(s.price) if s.price else 0.0,
                'description': s.description if s.description else ''
            })

        return jsonify({
            'message': 'Catálogo de servicios adicionales obtenido con éxito',
            'data': services_list,
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al obtener el catálogo de servicios en el servidor',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/services/order', methods=['POST'])
@jwt_required()
def order_additional_service():
    """
    Endpoint para Solicitar un Servicio Extra.

    POST /apis/v1/services/order
    Registra de manera atómica un nuevo cargo o consumo a la habitación del huésped.
    Multiplica la cantidad por el precio unitario del servicio para calcular el subtotal.

    ---
    Estructura del JSON esperado (Request Body):
        {
            "reservation_id": "res_123456",
            "service_id": "srv_789101",
            "quantity": 2
        }

    Estructura del JSON de Retorno con Éxito (Status 201):
        {
            "success": true,
            "message": "Servicio adicional registrado y cargado a la habitación con éxito",
            "error": null,
            "data": {
                "id": "string (UML: id_reservation_service)",
                "reservation_id": "string",
                "service_id": "string",
                "quantity": int,
                "subtotal": float
            }
        }
    """
    data = request.get_json()
    if not data or 'reservation_id' not in data or 'service_id' not in data:
        return jsonify({
            'message': 'Los parámetros reservation_id y service_id son obligatorios',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400

    session = Session()
    try:
        reservation_id = data.get('reservation_id')
        service_id = data.get('service_id')
        quantity = int(data.get('quantity', 1))

        # Validación preventiva: Comprobamos la existencia física de la reserva
        res = session.query(Reservation).filter(Reservation.id_reservation == reservation_id).first()
        if not res:
            return jsonify({
                'message': 'La reserva especificada no existe',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        # Validación preventiva: Comprobamos la existencia del servicio solicitado
        srv = session.query(Service).filter(Service.id_service == service_id).first()
        if not srv:
            return jsonify({
                'message': 'El servicio solicitado no está disponible en el catálogo',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        # Cálculo de negocio para el subtotal relacional
        subtotal_calculado = float(srv.price) * quantity

        # Generación de la PK del consumo extra
        res_service_id = f"rsv_srv_{int(datetime.utcnow().timestamp())}"

        # Inserción atómica respetando las columnas del modelo UML
        new_order = ReservationService(
            id_reservation_service=res_service_id,
            reservation_id=reservation_id,
            service_id=service_id,
            quantity=quantity,
            subtotal=subtotal_calculado
        )

        session.add(new_order)
        session.commit()

        return jsonify({
            'message': 'Servicio adicional registrado y cargado a la habitación con éxito',
            'data': {
                'id': new_order.id_reservation_service,
                'reservation_id': new_order.reservation_id,
                'service_id': new_order.service_id,
                'quantity': new_order.quantity,
                'subtotal': float(new_order.subtotal)
            },
            'success': True, 'error': None
        }), 201

    except Exception as e:
        session.rollback()  # Revierte la transacción contable si la BD experimenta fallos de consistencia
        traceback.print_exc()
        return jsonify({
            'message': 'Error al procesar el cargo del servicio extra',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/services/room-consumptions/<string:reservation_id>', methods=['GET'])
@jwt_required()
def get_room_consumptions(reservation_id):
    """
    Endpoint para el Historial de Consumos de una Habitación.

    GET /apis/v1/services/room-consumptions/<reservation_id>
    Obtiene todos los consumos adicionales aplicados a una estadía específica.
    Optimiza el rendimiento de la red mediante cargas combinadas en una sola consulta SQL.

    ---
    Cabeceras Requeridas (Headers):
        - Authorization: Bearer <JWT_TOKEN>
    """
    session = Session()
    try:
        # Usamos joinedload para pre-cargar la relación 'service' y evitar el problema de consultas N+1
        items = (
            session.query(ReservationService)
            .options(joinedload(ReservationService.service))
            .filter(ReservationService.reservation_id == reservation_id)
            .all()
        )
        
        data_response = []
        for item in items:
            data_response.append({
                'id': item.id_reservation_service,
                'reservation_id': item.reservation_id,
                'quantity': item.quantity,
                'subtotal': float(item.subtotal) if item.subtotal else 0.0,
                'service': {
                    'id': item.service.id_service if item.service else None,
                    'name': item.service.name if item.service else 'Servicio Desconocido',
                    'price': float(item.service.price) if (item.service and item.service.price) else 0.0
                }
            })
        
        return jsonify({
            'message': 'Consumos extras de la habitación obtenidos correctamente',
            'data': data_response,
            'success': True, 'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al obtener los consumos de la habitación',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()