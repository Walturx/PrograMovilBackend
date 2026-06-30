import traceback
from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from main.database import Session
from main.models import Reservation, Room, Payment, User, LoyaltyTransaction

api = Blueprint('hotel_ya_apis_payments', __name__)


@api.route('/apis/v1/payments/qr/<string:reservation_id>', methods=['GET'])
@jwt_required()
def generate_payment_qr(reservation_id):
    """Genera el string que se pinta como QR para pagar una reserva pendiente."""
    session = Session()
    try:
        res = session.query(Reservation).filter_by(id_reservation=reservation_id).first()
        if not res:
            return jsonify({'success': False, 'message': 'Reserva no encontrada'}), 404

        qr_string = f"hotelya.payment.qr_res_{res.id_reservation}_amount_{float(res.total_price)}"
        return jsonify({'success': True, 'message': 'OK', 'data': {
            'reservation_id': res.id_reservation,
            'qr_string': qr_string,
            'amount': float(res.total_price)
        }}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al generar QR', 'error': str(e)}), 500
    finally:
        session.close()


@api.route('/apis/v1/payments/verify/<string:reservation_id>', methods=['POST'])
@jwt_required()
def verify_payment_status(reservation_id):
    """Confirma el pago: marca la reserva, ocupa la habitación y suma estrellas."""
    session = Session()
    try:
        res = session.query(Reservation).filter_by(id_reservation=reservation_id).first()
        if not res:
            return jsonify({'success': False, 'message': 'Reserva no encontrada'}), 404

        if res.status == 'confirmed':
            return jsonify({'success': True, 'message': 'Ya estaba confirmada', 'data': {'status': 'confirmed'}}), 200

        res.status = 'confirmed'

        room = session.query(Room).filter_by(id_room=res.room_id).first()
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

        stars_awarded = 0
        stars_total = 0
        user = session.query(User).filter_by(id_user=res.user_id).first()
        if user:
            stars_awarded = (int(res.adults or 0) + int(res.children or 0)) + 3
            stars_total = int(user.stars_available or 0) + stars_awarded
            user.stars_available = stars_total

            session.add(LoyaltyTransaction(
                id_loyalty_transaction=f"lt_{ts}",
                user_id=user.id_user,
                reservation_id=res.id_reservation,
                reward_redemption_id=None,
                type='earned',
                stars=stars_awarded,
                description=f"Estrellas por reserva {res.id_reservation}",
                created_at=datetime.utcnow()
            ))

        session.commit()
        return jsonify({'success': True, 'message': 'Pago verificado', 'data': {
            'status': 'confirmed',
            'stars_awarded': stars_awarded,
            'stars_total': stars_total
        }}), 200

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error al verificar el pago', 'error': str(e)}), 500
    finally:
        session.close()