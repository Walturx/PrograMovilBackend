# ==============================================================================
# ARCHIVO: hotel_ya/apis/payments.py
# PROPÓSITO: Este módulo centraliza los endpoints transaccionales del motor de
#            pagos dentro del ecosistema "Hotel Ya". Administra la generación de
#            cadenas legibles para QR dinámicos y el procesamiento posterior de 
#            verificación bancaria, asegurando la consistencia e inyección de
#            estrellas de fidelidad en la cuenta del cliente de manera atómica.
# ==============================================================================

import traceback
from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from main.database import Session
from main.models import Reservation, Room, Payment, User, LoyaltyTransaction

# Creación del Blueprint para registrar el módulo financiero en Flask
api = Blueprint('hotel_ya_apis_payments', __name__)

@api.route('/apis/v1/payments/qr/<string:reservation_id>', methods=['GET'])
@jwt_required()
def generate_payment_qr(reservation_id):
    """
    Endpoint para Generación de QR de Pago.

    GET /apis/v1/payments/qr/<reservation_id>
    Simula la generación de la cadena de pago interoperable (BPI) 
    para pintar el código QR dinámico de la pasarela en Flutter.

    ---
    Parámetros de Ruta (Path Parameters):
        - reservation_id (string): El ID de la pre-reserva (UML: id_reservation).
    """
    session = Session()
    try:
        # Búsqueda estricta usando id_reservation conforme a las propiedades físicas de la BD
        res = session.query(Reservation).filter(Reservation.id_reservation == reservation_id).first()
        
        if not res:
            return jsonify({
                'message': 'No se encontró la reserva',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404

        # Construcción de la trama estándar interoperable simulada
        qr_data = f"hotelya.payment.qr_res_{res.id_reservation}_amount_{float(res.total_price)}"

        return jsonify({
            'message': 'Datos del QR de pago generados con éxito',
            'data': {
                'reservation_id': res.id_reservation,
                'qr_string': qr_data,
                'amount': float(res.total_price)
            },
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al generar los datos del QR de pago',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        # 💡 CORRECCIÓN CRÍTICA: Se inyectó el bloque finally para liberar la conexión a la base de datos
        session.close()


@api.route('/apis/v1/payments/verify/<string:reservation_id>', methods=['POST'])
@jwt_required()
def verify_payment_status(reservation_id):
    """
    Endpoint de Confirmación y Simulación de Pasarela Bancaria.

    POST /apis/v1/payments/verify/<reservation_id>
    Recibe el llamado de confirmación. Cambia el estado de la reserva a 'confirmed',
    marca la habitación como ocupada/no disponible y calcula las estrellas ganadas.
    """
    session = Session()
    try:
        res = session.query(Reservation).filter(Reservation.id_reservation == reservation_id).first()
        if not res:
            return jsonify({
                'message': 'No se encontró la reserva solicitada para verificación',
                'data': None, 
                'success': False, 
                'error': 'Not Found'
            }), 404

        if res.status == 'confirmed':
            return jsonify({
                'message': 'Esta reserva ya ha sido pagada y confirmada previamente',
                'data': {'status': res.status},
                'success': True, 
                'error': None
            }), 200

        # 1. Transicionar de forma segura el estado de la reserva a Confirmada
        res.status = "confirmed"

        # 2. Actualizar el inventario físico: La habitación ya no está disponible
        room = session.query(Room).filter(Room.id_room == res.room_id).first()
        if room:
            room.is_available = False

        # 3. Registrar el comprobante contable en la tabla 'payments'
        pay_id = f"pay_{int(datetime.utcnow().timestamp())}"
        new_payment = Payment(
            id_payment=pay_id,
            reservation_id=res.id_reservation,
            amount=res.total_price,
            payment_method="QR_BPI",
            status="completed",
            transaction_date=datetime.utcnow()
        )
        session.add(new_payment)

        # 4. Motor de Lealtad: Inyección de estrellas por fidelización (1 estrella por cada 10 unidades de precio)
        user = session.query(User).filter(User.id_user == res.user_id).first()
        if user:
            estrellas_ganadas = int(res.total_price // 10)
            
            # 💡 CORRECCIÓN PREVENTIVA: Evitamos errores matemáticos si el usuario tiene Null de forma nativa
            stars_actuales = int(getattr(user, 'stars_available', 0) or 0)
            user.stars_available = stars_actuales + estrellas_ganadas
            
            # Registramos el movimiento detallado en la tabla contable 'loyalty_transactions'
            txn_id = f"lt_{int(datetime.utcnow().timestamp())}"
            new_txn = LoyaltyTransaction(
                id_loyalty_transaction=txn_id,
                user_id=user.id_user,
                reservation_id=res.id_reservation,
                reward_redemption_id=None,
                type="earned",
                stars=estrellas_ganadas,
                description=f"Estrellas ganadas por estadía en Reserva {res.id_reservation}",
                created_at=datetime.utcnow()
            )
            session.add(new_txn)

        # Confirmación completa de todas las inserciones y mutaciones relacionales
        session.commit()

        return jsonify({
            'message': 'Estado del pago verificado y procesado correctamente',
            'data': {'status': res.status},
            'success': True, 
            'error': None
        }), 200

    except Exception as e:
        session.rollback()  # Garantiza que el dinero, inventario y fidelización no queden corruptos si falla la BD
        traceback.print_exc()
        return jsonify({
            'message': 'Error al procesar la verificación del pago',
            'data': None, 
            'success': False, 
            'error': str(e)
        }), 500
    finally:
        session.close()