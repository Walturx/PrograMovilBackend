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


def parse_fecha(valor):
    """Convierte un string de fecha a datetime (la columna es DateTime y SQLite exige datetime).
    Acepta 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS'. Si ya es datetime, lo devuelve tal cual."""
    if isinstance(valor, datetime):
        return valor
    if not valor:
        return None
    for formato in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(valor), formato)
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha inválido: {valor}. Usa YYYY-MM-DD.")


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
            check_in=parse_fecha(data['check_in']),
            check_out=parse_fecha(data['check_out']),
            total_price=data.get('total_price', 0.0),
            status='pending',
            adults=data.get('adults', 1),
            children=data.get('children', 0),
            special_requests=data.get('special_requests', ''),
            created_at=datetime.utcnow()
        ))

        for i, g in enumerate(data.get('guests', [])):
            # Mapeo a las columnas REALES del modelo Guest (name/lastname/...).
            # Aceptamos tanto first_name/last_name (como envía Flutter) como name/lastname.
            session.add(Guest(
                id_guest=f"gst_{ts}_{i}",
                reservation_id=res_id,
                name=g.get('first_name') or g.get('name'),
                lastname=g.get('last_name') or g.get('lastname'),
                document_type=g.get('document_type', 'DNI'),
                document_number=g.get('document_number'),
                nationality=g.get('nationality')
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
                    {'name': g.name, 'lastname': g.lastname,
                     'document_type': g.document_type,
                     'document_number': g.document_number,
                     'nationality': g.nationality}
                    for g in guests
                ]
            })

        return jsonify({'success': True, 'message': 'OK', 'data': data}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al obtener historial', 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/reservations/<string:reservation_id>', methods=['GET'])
@jwt_required()
def get_reservation_detail(reservation_id):
    """
    Detalle de UNA reserva del usuario autenticado.

    GET /apis/v1/reservations/<reservation_id>
    Devuelve la reserva con su habitación, tipo de habitación y acompañantes.
    Solo el dueño de la reserva puede consultarla (seguridad por propiedad).
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        reservation = (
            session.query(Reservation)
            .filter_by(id_reservation=reservation_id)
            .first()
        )

        if not reservation:
            return jsonify({'success': False, 'message': 'Reserva no encontrada', 'data': None}), 404

        # Seguridad: la reserva debe pertenecer al usuario del token
        if str(reservation.user_id) != str(user_id):
            return jsonify({'success': False, 'message': 'No autorizado para ver esta reserva', 'data': None}), 403

        room = session.query(Room).filter_by(id_room=reservation.room_id).first()
        room_type = (
            session.query(RoomType).filter_by(id_room_type=room.room_type_id).first()
            if room else None
        )
        guests = session.query(Guest).filter_by(reservation_id=reservation.id_reservation).all()

        data = {
            'id': reservation.id_reservation,
            'status': reservation.status,
            'check_in': fmt(reservation.check_in),
            'check_out': fmt(reservation.check_out),
            'total_price': float(reservation.total_price or 0),
            'adults': reservation.adults,
            'children': reservation.children,
            'special_requests': reservation.special_requests or '',
            'created_at': fmt(reservation.created_at),
            'room': {
                'id': room.id_room,
                'hotel_id': room.hotel_id,
                'room_number': room.room_number,
                'floor': room.floor,
                'image_url': room.image_url or '',
                'room_type': {
                    'id': room_type.id_room_type,
                    'name': room_type.name,
                    'base_price': float(room_type.base_price or 0),
                    'capacity': room_type.capacity
                } if room_type else None
            } if room else None,
            # Leemos los acompañantes con los nombres REALES de columna del modelo Guest
            'guests': [
                {
                    'name': g.name,
                    'lastname': g.lastname,
                    'document_type': g.document_type,
                    'document_number': g.document_number,
                    'nationality': g.nationality
                }
                for g in guests
            ]
        }

        return jsonify({'success': True, 'message': 'OK', 'data': data}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al obtener el detalle de la reserva', 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/rooms/availability', methods=['GET'])
def get_available_rooms():
    """
    Habitaciones disponibles para un rango de fechas.

    GET /apis/v1/rooms/availability?check_in=YYYY-MM-DD&check_out=YYYY-MM-DD&hotel_id=<opcional>
    Devuelve las habitaciones que no tienen ninguna reserva activa que se cruce
    con el rango solicitado. Endpoint público (para mostrar el buscador en Flutter).
    """
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    hotel_id = request.args.get('hotel_id')

    if not check_in or not check_out:
        return jsonify({'success': False, 'message': 'check_in y check_out son obligatorios'}), 400
    if check_in >= check_out:
        return jsonify({'success': False, 'message': 'check_out debe ser posterior a check_in'}), 400

    session = Session()
    try:
        # Habitaciones candidatas: marcadas como disponibles (y del hotel, si se filtra)
        rooms_query = session.query(Room).filter(Room.is_available == True)
        if hotel_id:
            rooms_query = rooms_query.filter(Room.hotel_id == hotel_id)
        rooms = rooms_query.all()

        # Reservas que bloquean fechas (todas menos las canceladas)
        blocking = (
            session.query(Reservation)
            .filter(Reservation.status != 'cancelled')
            .all()
        )

        # Un rango [a_in, a_out) se cruza con [b_in, b_out) si  a_in < b_out  y  b_in < a_out
        busy_room_ids = set()
        for r in blocking:
            r_in, r_out = fmt(r.check_in)[:10], fmt(r.check_out)[:10]
            if check_in < r_out and r_in < check_out:
                busy_room_ids.add(r.room_id)

        available = []
        for room in rooms:
            if room.id_room in busy_room_ids:
                continue
            rt = session.query(RoomType).filter_by(id_room_type=room.room_type_id).first()
            available.append({
                'id': room.id_room,
                'hotel_id': room.hotel_id,
                'room_number': room.room_number,
                'floor': room.floor,
                'image_url': room.image_url or '',
                'room_type': {
                    'id': rt.id_room_type,
                    'name': rt.name,
                    'base_price': float(rt.base_price or 0),
                    'capacity': rt.capacity
                } if rt else None
            })

        return jsonify({
            'success': True,
            'message': f'{len(available)} habitaciones disponibles',
            'data': {
                'check_in': check_in,
                'check_out': check_out,
                'rooms': available
            }
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al consultar disponibilidad', 'error': str(e)}), 500
    finally:
        session.close()