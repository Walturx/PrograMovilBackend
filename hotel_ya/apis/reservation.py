import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import Reservation, Room, RoomType, Guest

api = Blueprint('hotel_ya_apis_reservations', __name__)

def fmt(fecha):
    """Convierte fechas a string, sin importar si vienen como datetime o ya como str."""
    if not fecha:
        return ''
    return fecha.strftime('%Y-%m-%d %H:%M:%S') if isinstance(fecha, datetime) else str(fecha)


@api.route('/apis/v1/room-types/<string:room_type_id>', methods=['GET'])
def get_room_type(room_type_id):
    """Datos de un tipo de habitación: nombre, precio base y capacidad."""
    session = Session()
    try:
        rt = session.query(RoomType).filter_by(id_room_type=room_type_id).first()
        if not rt:
            return jsonify({'success': False, 'message': 'Tipo de habitación no encontrado', 'data': None}), 404

        return jsonify({'success': True, 'message': 'OK', 'data': {
            'id': rt.id_room_type,
            'name': rt.name,
            'description': rt.description or '',
            'base_price': float(rt.base_price or 0),
            'capacity': rt.capacity
        }}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al cargar tipo de habitación', 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """Crea una reserva en estado 'pending' junto con sus acompañantes."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    if not all(k in data for k in ('room_id', 'check_in', 'check_out')):
        return jsonify({'success': False, 'message': 'room_id, check_in y check_out son obligatorios'}), 400

    session = Session()
    try:
        room = session.query(Room).filter_by(id_room=data['room_id']).first()
        if not room:
            return jsonify({'success': False, 'message': 'Habitación no encontrada'}), 404
        if not room.is_available:
            return jsonify({'success': False, 'message': 'Habitación no disponible'}), 409

        ts = int(datetime.utcnow().timestamp())
        res_id = f"res_{ts}"

        session.add(Reservation(
            id_reservation=res_id,
            user_id=str(user_id),
            room_id=room.id_room,
            check_in=data['check_in'],
            check_out=data['check_out'],
            total_price=data.get('total_price', 0.0),
            status='pending',
            adults=data.get('adults', 1),
            children=data.get('children', 0),
            special_requests=data.get('special_requests', ''),
            created_at=datetime.utcnow()
        ))

        for i, g in enumerate(data.get('guests', [])):
            session.add(Guest(
                id_guest=f"gst_{ts}_{i}",
                reservation_id=res_id,
                first_name=g.get('first_name'),
                last_name=g.get('last_name'),
                document_number=g.get('document_number'),
                age=g.get('age', 18)
            ))

        session.commit()
        return jsonify({'success': True, 'message': 'Reserva creada', 'data': {
            'id': res_id,
            'total_price': data.get('total_price', 0.0),
            'status': 'pending'
        }}), 201

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al crear la reserva', 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations', methods=['GET'])
@jwt_required()
def get_my_reservations():
    """Historial de reservas del usuario autenticado, con sus acompañantes."""
    user_id = get_jwt_identity()
    session = Session()
    try:
        reservations = (
            session.query(Reservation)
            .filter_by(user_id=str(user_id))
            .order_by(Reservation.created_at.desc())
            .all()
        )

        data = []
        for r in reservations:
            guests = session.query(Guest).filter_by(reservation_id=r.id_reservation).all()
            data.append({
                'id': r.id_reservation,
                'room_id': r.room_id,
                'check_in': fmt(r.check_in),
                'check_out': fmt(r.check_out),
                'total_price': float(r.total_price or 0),
                'status': r.status,
                'adults': r.adults,
                'children': r.children,
                'special_requests': r.special_requests or '',
                'created_at': fmt(r.created_at),
                'guests': [
                    {'first_name': g.first_name, 'last_name': g.last_name,
                     'document_number': g.document_number, 'age': g.age}
                    for g in guests
                ]
            })

        return jsonify({'success': True, 'message': 'OK', 'data': data}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al obtener historial', 'error': str(e)}), 500
    finally:
        session.close()