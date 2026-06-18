# hotel_ya\apis\loyalty.py
import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import User, Reward, RewardRedemption, LoyaltyTransaction

api = Blueprint('hotel_ya_apis_loyalty', __name__)

@api.route('/apis/v1/loyalty/rewards', methods=['GET'])
def get_active_rewards():
    """
    Lista los premios y beneficios disponibles en el catálogo del hotel.
    """
    session = Session()
    try:
        rewards = session.query(Reward).filter(Reward.is_active == True).all()
        return jsonify({
            'message': 'Catálogo de premios obtenido',
            'data': [r.to_dict() for r in rewards],
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al obtener el catálogo de premios',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/loyalty/redeem', methods=['POST'])
@jwt_required()
def redeem_reward():
    """
    Procesa de manera transaccional el canje de un premio utilizando las estrellas del usuario.
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'rewardId' not in data:
        return jsonify({
            'message': 'El parámetro rewardId es obligatorio',
            'data': None, 'success': False, 'error': 'Bad Request'
        }), 400

    reward_id = data['rewardId']
    reservation_id = data.get('reservationId') # Opcional según el diagrama

    session = Session()
    try:
        # Verificar usuario y sus estrellas disponibles
        user = session.query(User).filter(User.id == str(user_id)).first()
        if not user:
            return jsonify({
                'message': 'Usuario no encontrado',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        # Verificar existencia y costo del premio
        reward = session.query(Reward).filter(Reward.id == reward_id, Reward.is_active == True).first()
        if not reward:
            return jsonify({
                'message': 'El premio solicitado no existe o no está activo',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        if user.stars_available < reward.stars_cost:
            return jsonify({
                'message': f'Estrellas insuficientes. Requieres {reward.stars_cost} y tienes {user.stars_available}',
                'data': None, 'success': False, 'error': 'Forbidden'
            }), 403

        # 1. Descontar las estrellas al usuario
        user.stars_available -= reward.stars_cost

        # 2. Registrar la redención (reward_redemptions)
        redemption_id = f"red_{int(datetime.utcnow().timestamp())}"
        new_redemption = RewardRedemption(
            id=redemption_id,
            user_id=user.id,
            reward_id=reward.id,
            reservation_id=reservation_id,
            stars_spent=reward.stars_cost,
            status="approved",
            created_at=datetime.utcnow()
        )
        session.add(new_redemption)

        # 3. Registrar el movimiento en el historial de transacciones (loyalty_transactions)
        new_transaction = LoyaltyTransaction(
            id=f"ltx_{int(datetime.utcnow().timestamp())}",
            user_id=user.id,
            reservation_id=reservation_id,
            reward_redemption_id=redemption_id,
            type="redemption",
            stars=-reward.stars_cost,
            description=f"Canje de premio: {reward.name}",
            created_at=datetime.utcnow()
        )
        session.add(new_transaction)

        session.commit()

        return jsonify({
            'message': f'¡Canje exitoso! Has obtenido {reward.name}',
            'data': {
                'redemption_id': redemption_id,
                'stars_remaining': user.stars_available
            },
            'success': True, 'error': None
        }), 201

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Error transaccional al procesar el canje',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/loyalty/history', methods=['GET'])
@jwt_required()
def get_loyalty_history():
    """
    Obtiene el historial completo de movimientos de estrellas (ganadas y gastadas) del usuario autenticado.
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        transactions = (
            session.query(LoyaltyTransaction)
            .filter(LoyaltyTransaction.user_id == str(user_id))
            .order_by(LoyaltyTransaction.created_at.desc())
            .all()
        )
        
        return jsonify({
            'message': 'Historial de lealtad obtenido correctamente',
            'data': [t.to_dict() for t in transactions],
            'success': True, 'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al consultar el historial de lealtad',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()