# hotel_ya\apis\rewards.py
import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from main.database import Session
from main.models import User, Reservation, Room, Reward, RewardRedemption
from main.application import REVOKED_TOKENS
from sqlalchemy.orm import joinedload

api = Blueprint('hotel_ya_apis_rewards', __name__)

@api.route('/apis/v1/users/me', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Endpoint para la pantalla '/profile'.
    Obtiene la información actualizada del perfil del cliente junto con sus estrellas disponibles.
    """
    response = None
    status = 200
    user_id = get_jwt_identity()
    
    session = Session()
    try:
        user = session.query(User).filter(User.id == str(user_id)).first()
        if not user:
            return jsonify({
                'message': 'No se encontró el registro del usuario',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        response = jsonify({
            'message': 'Perfil de usuario cargado con éxito',
            'data': user.to_dict(), # Sincronizado al 100% con tu UserModel de Flutter
            'success': True, 'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Error al recuperar la información del perfil',
            'data': None, 'success': False, 'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/users/me/reservations', methods=['GET'])
@jwt_required()
def get_reservation_history():
    """
    Endpoint para la pantalla '/history'.
    Retorna el historial completo de viajes consumidos y agendados por el usuario actual.
    """
    response = None
    status = 200
    user_id = get_jwt_identity()
    
    session = Session()
    try:
        # Usamos joinedload anidado para traer el hotel asociado a la habitación eficientemente
        reservations = (
            session.query(Reservation)
            .options(joinedload(Reservation.room).joinedload(Room.hotel))
            .filter(Reservation.user_id == str(user_id))
            .all()
        )
        
        res_list = [r.to_dict() for r in reservations]

        response = jsonify({
            'message': 'Historial de reservas del usuario obtenido',
            'data': res_list,
            'success': True, 'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Error al cargar el historial de viajes',
            'data': None, 'success': False, 'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/rewards', methods=['GET'])
def get_rewards_catalog():
    """
    Endpoint para la pantalla '/rewards'.
    Lista el catálogo público de todos los premios activos de la tienda de fidelidad.
    """
    response = None
    status = 200
    session = Session()
    try:
        rewards = session.query(Reward).filter(Reward.is_active == True).all()
        rewards_list = [rw.to_dict() for rw in rewards]

        response = jsonify({
            'message': 'Catálogo de premios de fidelidad cargado',
            'data': rewards_list,
            'success': True, 'error': None
        })
    except Exception as e:
        traceback.print_exc()
        response = jsonify({
            'message': 'Error al consultar la lista de beneficios',
            'data': None, 'success': False, 'error': str(e)
        })
        status = 500
    finally:
        session.close()

    return response, status


@api.route('/apis/v1/rewards/redeem', methods=['POST'])
@jwt_required()
def redeem_reward():
    """
    Endpoint para la pantalla del QR de Beneficio ('/qr').
    Valida los saldos, debita transaccionalmente las estrellas del perfil y genera la redención.
    """
    data = request.get_json()
    if not data or 'reward_id' not in data:
        return jsonify({
            'message': 'Falta el parámetro obligatorio reward_id',
            'data': None, 'success': False, 'error': 'Bad Request'
        }), 400

    user_id = get_jwt_identity()
    session = Session()
    try:
        user = session.query(User).filter(User.id == str(user_id)).first()
        reward = session.query(Reward).filter(Reward.id == str(data['reward_id'])).first()

        if not user or not reward:
            return jsonify({
                'message': 'No se encontraron registros válidos para el canje',
                'data': None, 'success': False, 'error': 'Not Found'
            }), 404

        # Validación del balance de estrellas acumuladas
        if user.stars_available < reward.stars_cost:
            return jsonify({
                'message': f"Estrellas insuficientes. Requieres {reward.stars_cost} y posees {user.stars_available}.",
                'data': None, 'success': False, 'error': 'Precondition Failed'
            }), 400

        # Operación transaccional segura
        user.stars_available -= reward.stars_cost
        redemption = RewardRedemption(
            id=f"red_{int(datetime.utcnow().timestamp())}",
            user_id=user.id,
            reward_id=reward.id,
            reservation_id=data.get('reservation_id'), # Vinculación opcional según tu diagrama
            stars_spent=reward.stars_cost,
            status="approved", # Consistente con los estados de tu lógica de negocio
            created_at=datetime.utcnow()
        )
        session.add(redemption)
        session.commit()

        return jsonify({
            'message': '¡Canje procesado con éxito! Escanea tu QR en la recepción.',
            'data': {
                'stars_remaining': user.stars_available,
                'redemption_id': redemption.id
            },
            'success': True, 'error': None
        }), 200

    except Exception as e:
        session.rollback() # Protege las estrellas del cliente si algo falla internamente
        traceback.print_exc()
        return jsonify({
            'message': 'Error transaccional al ejecutar el canje',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/users/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Endpoint complementario dentro de '/profile'.
    Invalida el token JWT agregándolo de inmediato a la lista negra en el backend.
    """
    try:
        jti = get_jwt()["jti"]
        REVOKED_TOKENS.append(jti)
        return jsonify({
            'message': 'Sesión finalizada exitosamente en el servidor',
            'data': None, 'success': True, 'error': None
        }), 200
    except Exception as e:
        return jsonify({
            'message': 'Error al revocar el token de acceso',
            'data': None, 'success': False, 'error': str(e)
        }), 500