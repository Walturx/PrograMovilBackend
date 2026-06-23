# ==============================================================================
# ARCHIVO: hotel_ya/apis/reservation.py
# PROPÓSITO: Este módulo centraliza los endpoints transaccionales del flujo de
#            reservas dentro del ecosistema "Hotel Ya". Administra la consulta de
#            metadatos de habitaciones, la inserción segura y atómica de nuevas 
#            reservas con múltiples huéspedes (Guests) y el listado del historial
#            completo de estancias del usuario para la aplicación en Flutter.
# ==============================================================================

import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import Reservation, Room, RoomType, Guest, User

# Creación del Blueprint para registrar el módulo en la arquitectura de Flask
api = Blueprint('hotel_ya_apis_reservations', __name__)

@api.route('/apis/v1/room-types/<string:room_type_id>', methods=['GET'])
def get_room_type(room_type_id):
    """
    Endpoint para Tipo de Habitación.

    GET /apis/v1/room-types/<room_type_id>
    Obtiene la información, precio base y capacidad máxima de un tipo de habitación específico.
    """
    session = Session()
    try:
        # Filtramos usando id_room_type conforme al esquema físico SQL real
        rt = session.query(RoomType).filter(RoomType.id_room_type == room_type_id).first()
        if not rt:
            return jsonify({
                'message': f'No se encontró el tipo de habitación con ID {room_type_id}',
                'data': None, 
                'success': False, 
                'error': 'Not Found'
            }), 404

        return jsonify({
            'message': 'Tipo de habitación cargado correctamente',
            'data': {
                'id': rt.id_room_type,
                'name': rt.name,
                'description': rt.description if rt.description else '',
                'base_price': float(rt.base_price) if rt.base_price else 0.0,
                'capacity': rt.capacity
            },
            'success': True, 
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al procesar la solicitud del tipo de habitación',
            'data': None, 
            'success': False, 
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    Endpoint Transaccional para Creación de Reservas.

    POST /apis/v1/reservations
    Genera un registro atómico de pre-reserva en estado 'pending' vinculando
    dinámicamente el listado de acompañantes obligatorios (Guests).
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'room_id' not in data or 'check_in' not in data or 'check_out' not in data:
        return jsonify({
            'message': 'Los campos room_id, check_in y check_out son obligatorios',
            'data': None, 
            'success': False, 
            'error': 'Bad Request'
        }), 400

    session = Session()
    try:
        # 1. Validar la existencia física y disponibilidad de la habitación elegida
        room = session.query(Room).filter(Room.id_room == data.get('room_id')).first()
        if not room:
            return jsonify({
                'message': 'La habitación seleccionada no existe',
                'data': None, 
                'success': False, 
                'error': 'Not Found'
            }), 404

        if not room.is_available:
            return jsonify({
                'message': 'La habitación ya no se encuentra disponible para reserva',
                'data': None, 
                'success': False, 
                'error': 'Conflict'
            }), 409

        # Generador de ID único transaccional basado en marcas de tiempo para SQLite
        timestamp_now = int(datetime.utcnow().timestamp())
        res_id = f"res_{timestamp_now}"

        # 2. Inserción de la cabecera de la Reserva en estado pendiente de pago
        new_reservation = Reservation(
            id_reservation=res_id,
            user_id=str(user_id),
            room_id=room.id_room,
            check_in=data.get('check_in'),
            check_out=data.get('check_out'),
            total_price=data.get('total_price', 0.0),
            status="pending",  # Esperando flujo QR financiero de payments.py
            adults=data.get('adults', 1),
            children=data.get('children', 0),
            special_requests=data.get('special_requests', ''),
            created_at=datetime.utcnow()
        )
        session.add(new_reservation)

        # 3. Registro iterativo de huéspedes adicionales (Acompañantes en Flutter)
        guests_input = data.get('guests', [])
        for index, g_data in enumerate(guests_input):
            guest_id = f"gst_{timestamp_now}_{index}"
            new_guest = Guest(
                id_guest=guest_id,
                reservation_id=res_id,
                first_name=g_data.get('first_name'),
                last_name=g_data.get('last_name'),
                document_number=g_data.get('document_number'),
                age=g_data.get('age', 18)
            )
            session.add(new_guest)

        # Confirmación atómica completa de la operación
        session.commit()

        return jsonify({
            'message': 'Pre-reserva creada con éxito. Proceda al módulo de pago.',
            'data': {
                'id': new_reservation.id_reservation,
                'total_price': float(new_reservation.total_price),
                'status': new_reservation.status
            },
            'success': True, 
            'error': None
        }), 201

    except Exception as e:
        session.rollback()  # Revierte todo el bloque relacional si algo falla para evitar inconsistencias
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error transaccional al procesar la reserva',
            'data': None, 
            'success': False, 
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations', methods=['GET'])
@jwt_required()
def get_my_reservations():
    """
    Endpoint para Historial de Estancias.

    GET /apis/v1/reservations
    Recupera el historial completo de estancias (activas, pasadas y pendientes)
    del usuario autenticado mapeado de manera limpia para los listados de Flutter.
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        reservations = (
            session.query(Reservation)
            .filter(Reservation.user_id == str(user_id))
            .order_by(Reservation.created_at.desc())
            .all()
        )
        
        res_list = []
        for r in reservations:
            # Control seguro de parseo para marcas de tiempo provenientes de SQLite
            if isinstance(r.created_at, datetime):
                fecha_str = r.created_at.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(r.created_at, str):
                fecha_str = r.created_at
            else:
                fecha_str = ''

            res_list.append({
                'id': r.id_reservation,
                'room_id': r.room_id,
                'check_in': r.check_in,
                'check_out': r.check_out,
                'total_price': float(r.total_price) if r.total_price else 0.0,
                'status': r.status,  # 'pending', 'confirmed', 'cancelled'
                'adults': r.adults,
                'children': r.children,
                'special_requests': r.special_requests if r.special_requests else '',
                'created_at': fecha_str
            })

        return jsonify({
            'message': 'Historial de reservas obtenido correctamente',
            'data': res_list,
            'success': True, 
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al consultar el historial de estancias',
            'data': None, 
            'success': False, 
            'error': str(e)
        }), 500
    finally:
        session.close()

