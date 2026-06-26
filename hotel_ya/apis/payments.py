import traceback
from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import Reservation, Room, Payment, User, LoyaltyTransaction

api = Blueprint('hotel_ya_apis_payments', __name__)

@api.route('/apis/v1/payments/qr/<string:reservation_id>', methods=['GET'])
@jwt_required()
def generate_payment_qr(reservation_id):
    session = Session()
    try:
        res = session.query(Reservation).filter(Reservation.id_reservation == reservation_id).first()
        if not res:
            return jsonify({'message': 'Reserva no encontrada', 'data': None, 'success': False, 'error': 'Not Found'}), 404

        qr_data = f"hotelya.payment.qr_res_{res.id_reservation}_amount_{float(res.total_price)}"
        return jsonify({'message': 'QR generado con éxito', 'data': {
            'reservation_id': res.id_reservation,
            'qr_string': qr_data,
            'amount': float(res.total_price)
        }, 'success': True, 'error': None}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'message': 'Error al generar QR', 'data': None, 'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/payments/verify/<string:reservation_id>', methods=['POST'])
@jwt_required()
def verify_payment_status(reservation_id):
    session = Session()
    try:
        res = session.query(Reservation).filter(Reservation.id_reservation == reservation_id).first()
        if not res:
            return jsonify({'message': 'Reserva no encontrada', 'data': None, 'success': False, 'error': 'Not Found'}), 404

        if res.status == 'confirmed':
            return jsonify({'message': 'Reserva ya confirmada previamente', 'data': {'status': res.status}, 'success': True, 'error': None}), 200

        res.status = 'confirmed'

        room = session.query(Room).filter(Room.id_room == res.room_id).first()
        if room:
            room.is_available = False

        ts = int(datetime.utcnow().timestamp())
        session.add(Payment(
            id_payment=f"pay_{ts}",
            reservation_id=res.id_reservation,
            amount=res.total_price,
            payment_method='QR_BPI',
            status='completed',
            transaction_date=datetime.utcnow()
        ))

        user = session.query(User).filter(User.id_user == res.user_id).first()
        if user:
            estrellas_ganadas = (int(res.adults or 0) + int(res.children or 0)) + 3
            user.stars_available = int(getattr(user, 'stars_available', 0) or 0) + estrellas_ganadas
            session.add(LoyaltyTransaction(
                id_loyalty_transaction=f"lt_{ts}",
                user_id=user.id_user,
                reservation_id=res.id_reservation,
                reward_redemption_id=None,
                type='earned',
                stars=estrellas_ganadas,
                description=f"Estrellas por reserva {res.id_reservation}",
                created_at=datetime.utcnow()
            ))

        session.commit()
        return jsonify({'message': 'Pago verificado y procesado', 'data': {
            'status': res.status,
            'stars_awarded': estrellas_ganadas,
            'stars_total': user.stars_available if user else 0
        }, 'success': True, 'error': None}), 200

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({'message': 'Error al verificar el pago', 'data': None, 'success': False, 'error': str(e)}), 500
    finally:
        session.close()