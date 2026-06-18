# hotel_ya\apis\reservation.py
import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import Reservation, Room, RoomType, Guest, Payment, User
from sqlalchemy.orm import joinedload

api = Blueprint('hotel_ya_apis_reservations', __name__)

@api.route('/apis/v1/room-types/<string:room_type_id>', methods=['GET'])
def get_room_type(room_type_id):
    """
    Endpoint para la pantalla '/reservation'.
    Obtiene la información y capacidad del tipo de habitación seleccionada.
    """
    response = None
    status = 200
    session = Session()
    try:
        rt = session.query(RoomType).filter(RoomType.id == room_type_id).first()
        if not rt:
            return jsonify({
                'message': f'No se encontró el tipo de habitación con ID {room_type_id}',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        response = jsonify({
            'message': 'Tipo de habitación cargado correctamente',
            'data': rt.to_dict(),
            'success': True, 'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Error al consultar el tipo de habitación',
            'data': None, 'success': False, 'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/rooms/<string:room_id>', methods=['GET'])
def get_room_status(room_id):
    """
    Endpoint para la pantalla '/reservation'.
    Verifica en tiempo real si la habitación en específico sigue estando libre.
    """
    response = None
    status = 200
    session = Session()
    try:
        room = session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return jsonify({
                'message': f'No se encontró la habitación con ID {room_id}',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        response = jsonify({
            'message': 'Disponibilidad verificada con éxito',
            'data': {
                'id': room.id,
                'room_number': room.room_number,
                'is_available': room.is_available
            },
            'success': True, 'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Error al verificar el estado de la habitación',
            'data': None, 'success': False, 'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/reservations/pre-calculate', methods=['POST'])
def pre_calculate():
    """
    Endpoint para la pantalla '/reservation/details'.
    Calcula de manera exacta los subtotales, impuestos y estrellas a ganar.
    """
    data = request.get_json()
    if not data or 'pricePerNight' not in data:
        return jsonify({
            'message': 'Falta el parámetro pricePerNight',
            'data': None, 'success': False, 'error': 'Bad Request'
        }), 400

    try:
        price_per_night = float(data.get('pricePerNight', 0))
        
        # Desglose matemático basado en tus parámetros de Flutter
        subtotal = price_per_night
        taxes = subtotal * 0.18  # 18% de impuesto estándar
        total = subtotal + taxes
        stars_earned = int(subtotal // 10)  # Gana 1 estrella por cada 10 unidades de precio base

        return jsonify({
            'message': 'Desglose financiero calculado correctamente',
            'data': {
                'subtotal': subtotal,
                'taxes': taxes,
                'total': total,
                'stars_earned': stars_earned
            },
            'success': True, 'error': None
        }), 200
    except Exception as e:
        return jsonify({
            'message': 'Ocurrió un error en el cálculo financiero',
            'data': None, 'success': False, 'error': str(e)
        }), 500


@api.route('/apis/v1/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """
    Endpoint para la pantalla '/payment'.
    Registra de manera transaccional la reserva inicial en estado 'pending' 
    e inserta de forma segura a todos los acompañantes (guests).
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'qrData' not in data or 'roomId' not in data:
        return jsonify({
            'message': 'Faltan parámetros obligatorios para registrar la reserva',
            'data': None, 'success': False, 'error': 'Bad Request'
        }), 400

    session = Session()
    try:
        # Instanciar la reserva usando el string ID del token JWT
        new_res = Reservation(
            id=data['qrData'],  # Identificador compartido con el QR
            user_id=str(user_id),
            room_id=data['roomId'],
            check_in=datetime.fromisoformat(data['checkIn'].replace('Z', '')),
            check_out=datetime.fromisoformat(data['checkOut'].replace('Z', '')),
            total_price=float(data['totalPrice']),
            adults=int(data.get('adults', 1)),
            children=int(data.get('children', 0)),
            special_requests=data.get('specialRequests', ''),
            status="pending",
            created_at=datetime.utcnow()
        )
        session.add(new_res)

        # Registro de acompañantes (guests) alineado con los modelos mapeados
        if 'guests' in data and isinstance(data['guests'], list):
            for idx, g in enumerate(data['guests']):
                guest = Guest(
                    id=f"gst_{int(datetime.utcnow().timestamp())}_{idx}",
                    reservation_id=new_res.id,
                    name=g.get('name', ''),
                    lastname=g.get('lastname', ''),
                    document_type=g.get('documentType', ''),
                    document_number=g.get('documentNumber', ''),
                    nationality=g.get('nationality', '')
                )
                session.add(guest)

        session.commit()

        return jsonify({
            'message': 'Reserva y acompañantes registrados correctamente',
            'data': {'reservation_id': new_res.id},
            'success': True, 'error': None
        }), 201

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Error transaccional al procesar la reserva',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/payments/qr/<string:reservation_id>', methods=['GET'])
def get_payment_qr(reservation_id):
    """
    Endpoint para la pantalla '/payment/qr'.
    Genera la cadena de datos correspondiente al código de pago.
    """
    return jsonify({
        'message': 'Datos del QR de pago generados',
        'data': {
            'qrData': f"HOTEL_YA_PAY_{reservation_id}",
            'status': 'pending_payment'
        },
        'success': True, 'error': None
    }), 200


@api.route('/apis/v1/payments/status/<string:reservation_id>', methods=['GET'])
def check_payment_status(reservation_id):
    """
    Endpoint para el Polling de la pantalla '/payment/qr'.
    Simula la aprobación del pago QR, actualizando la ocupación del cuarto 
    y abonando los puntos de fidelidad (estrellas) al usuario.
    """
    session = Session()
    try:
        res = session.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not res:
            return jsonify({
                'message': 'No se encontró el registro de la reserva solicitada',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        # Simulación de aprobación de pasarela
        if res.status == "pending":
            res.status = "confirmed"
            
            # Cambiamos el estado de la habitación asociada
            if res.room:
                res.room.is_available = False

            # Registramos el pago aprobado en la tabla de pagos
            pay = Payment(
                id=f"pay_{int(datetime.utcnow().timestamp())}",
                reservation_id=res.id,
                amount=res.total_price,
                method="QR",
                status="paid",
                paid_at=datetime.utcnow(),
                transaction_id=f"tx_{int(datetime.utcnow().timestamp())}"
            )
            session.add(pay)

            # Otorgamos las estrellas de fidelidad acumuladas en el usuario
            user = session.query(User).filter(User.id == res.user_id).first()
            if user:
                user.stars_available += int(res.total_price // 10)

            session.commit()

        return jsonify({
            'message': 'Consulta de estado de pago procesada',
            'data': {'status': res.status},
            'success': True, 'error': None
        }), 200

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Error al verificar o actualizar el estado del pago',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()