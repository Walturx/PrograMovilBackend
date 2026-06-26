import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import Reservation, Room, RoomType, Guest

api = Blueprint('hotel_ya_apis_reservations', __name__)

@api.route('/apis/v1/room-types/<string:room_type_id>', methods=['GET'])
def get_room_type(room_type_id):
    session = Session()
    try:
        rt = session.query(RoomType).filter(RoomType.id_room_type == room_type_id).first()
        if not rt:
            return jsonify({'message': f'Tipo de habitación {room_type_id} no encontrado', 'data': None, 'success': False, 'error': 'Not Found'}), 404
        return jsonify({'message': 'Tipo de habitación cargado', 'data': {
            'id': rt.id_room_type,
            'name': rt.name,
            'description': rt.description or '',
            'base_price': float(rt.base_price) if rt.base_price else 0.0,
            'capacity': rt.capacity
        }, 'success': True, 'error': None}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': 'Error al cargar tipo de habitación', 'data': None, 'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'room_id' not in data or 'check_in' not in data or 'check_out' not in data:
        return jsonify({'message': 'room_id, check_in y check_out son obligatorios', 'data': None, 'success': False, 'error': 'Bad Request'}), 400

    session = Session()
    try:
        room = session.query(Room).filter(Room.id_room == data.get('room_id')).first()
        if not room:
            return jsonify({'message': 'Habitación no encontrada', 'data': None, 'success': False, 'error': 'Not Found'}), 404
        if not room.is_available:
            return jsonify({'message': 'Habitación no disponible', 'data': None, 'success': False, 'error': 'Conflict'}), 409

        ts = int(datetime.utcnow().timestamp())
        res_id = f"res_{ts}"

        reservation = Reservation(
            id_reservation=res_id,
            user_id=str(user_id),
            room_id=room.id_room,
            check_in=data.get('check_in'),
            check_out=data.get('check_out'),
            total_price=data.get('total_price', 0.0),
            status='pending',
            adults=data.get('adults', 1),
            children=data.get('children', 0),
            special_requests=data.get('special_requests', ''),
            created_at=datetime.utcnow()
        )
        session.add(reservation)

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
        return jsonify({'message': 'Pre-reserva creada. Proceda al pago.', 'data': {
            'id': reservation.id_reservation,
            'total_price': float(reservation.total_price),
            'status': reservation.status
        }, 'success': True, 'error': None}), 201

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({'message': 'Error al crear la reserva', 'data': None, 'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations', methods=['GET'])
@jwt_required()
def get_my_reservations():
    user_id = get_jwt_identity()
    session = Session()
    try:
        reservations = (
            session.query(Reservation)
            .filter(Reservation.user_id == str(user_id))
            .order_by(Reservation.created_at.desc())
            .all()
        )

        def fmt_date(d):
            if isinstance(d, datetime): return d.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(d, str): return d
            return ''

        res_list = []
        for r in reservations:
            guests = session.query(Guest).filter(Guest.reservation_id == r.id_reservation).all()
            res_list.append({
                'id':               r.id_reservation,
                'room_id':          r.room_id,
                'check_in':         r.check_in,
                'check_out':        r.check_out,
                'total_price':      float(r.total_price) if r.total_price else 0.0,
                'status':           r.status,
                'adults':           r.adults,
                'children':         r.children,
                'special_requests': r.special_requests or '',
                'created_at':       fmt_date(r.created_at),
                'guests': [{'first_name': g.first_name, 'last_name': g.last_name, 'document_number': g.document_number, 'age': g.age} for g in guests]
            })

        return jsonify({'message': 'Historial obtenido correctamente', 'data': res_list, 'success': True, 'error': None}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': 'Error al obtener historial', 'data': None, 'success': False, 'error': str(e)}), 500
    finally:
        session.close()