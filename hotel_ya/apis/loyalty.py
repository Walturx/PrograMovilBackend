# ==============================================================================
# ARCHIVO: hotel_ya/apis/loyalty.py
# PROPÓSITO: Este módulo centraliza las operaciones del programa de fidelización
#            "Hotel Ya". Administra el catálogo de premios, el historial de 
#            transacciones de estrellas y el proceso de canje atómico (redención)
#            de recompensas mediante el descuento seguro de puntos del usuario.
# ==============================================================================

import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import User, Reward, RewardRedemption, LoyaltyTransaction
from sqlalchemy.orm import joinedload

# Creación del Blueprint para registrar el módulo de lealtad en Flask
api = Blueprint('hotel_ya_apis_loyalty', __name__)

@api.route('/apis/v1/loyalty/rewards', methods=['GET'])
def get_active_rewards():
    """
    Endpoint para el Catálogo de Premios Disponibles.

    GET /apis/v1/loyalty/rewards
    Obtiene la lista de recompensas físicas vigentes en el sistema.
    """
    session = Session()
    try:
        if session.query(Reward).count() == 0:
            premios_fuerza = [
                Reward(id_reward='rw1', name='Helado Premium', description='Helado gratis', stars_cost=5, type='food', is_active=True),
                Reward(id_reward='rw2', name='Chicha Gratis', description='Bebida gratis', stars_cost=4, type='drink', is_active=True),
                Reward(id_reward='rw3', name='1 Noche Gratis', description='Hospedaje gratis', stars_cost=30, type='hotel', is_active=True)
            ]
            session.add_all(premios_fuerza)
            session.commit()
            
        # Consulta directa y real a la base de datos
        rewards = session.query(Reward).filter(Reward.is_active == True).all()
        
        # 🔍 IMPRESIÓN DE CONTROL: Verás esto en la consola donde corre Flask
        print(f"\n[DEBUG BD] Se encontraron {len(rewards)} premios activos en SQLite.")
        
        rewards_list = []
        for r in rewards:
            rewards_list.append({
                'id': r.id_reward,
                'name': r.name,
                'description': r.description if r.description else '',
                'stars_cost': int(r.stars_cost),
                'type': r.type if r.type else 'General',
                'is_active': bool(r.is_active)
            })
            
        return jsonify({
            'message': 'Catálogo de premios obtenido correctamente',
            'data': rewards_list, 
            'success': True, 
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al cargar el catálogo de premios',
            'data': None, 
            'success': False, 
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/loyalty/redeem', methods=['POST'])
@jwt_required()
def redeem_reward():
    """
    Endpoint Transaccional para Canje de Premios.

    POST /apis/v1/loyalty/redeem
    Cuerpo esperado (JSON Body):
    {
        "reward_id": "rew_12345",
        "reservation_id": "res_67890"  [Opcional]
    }
    """
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'reward_id' not in data:
        return jsonify({
            'message': 'El identificador del premio (reward_id) es obligatorio',
            'data': None, 
            'success': False, 
            'error': 'Bad Request'
        }), 400

    reward_id = data.get('reward_id')
    reservation_id = data.get('reservation_id')  # Puede venir nulo desde la app

    session = Session()
    try:
        # 1. Obtener y validar la existencia del premio
        reward = session.query(Reward).filter(Reward.id_reward == reward_id, Reward.is_active == True).first()
        if not reward:
            return jsonify({
                'message': 'El premio seleccionado no existe o no se encuentra activo',
                'data': None, 
                'success': False, 
                'error': 'Not Found'
            }), 404

        # 2. Obtener el registro del usuario autenticado
        user = session.query(User).filter(User.id_user == str(user_id)).first()
        if not user:
            return jsonify({
                'message': 'Usuario no encontrado en el sistema',
                'data': None, 
                'success': False, 
                'error': 'Not Found'
            }), 404

        # Validación dinámica del saldo de estrellas usando el atributo correcto
        stars_actuales = int(getattr(user, 'stars_available', 0) or 0)
        costo_premio = int(reward.stars_cost)

        if stars_actuales < costo_premio:
            return jsonify({
                'message': f'Estrellas insuficientes. Requieres {costo_premio} y posees {stars_actuales}.',
                'data': None, 
                'success': False, 
                'error': 'Forbidden'
            }), 403

        # 3. Procesar el descuento seguro de estrellas en el modelo de usuario
        user.stars_available = stars_actuales - costo_premio

        # Generar IDs únicos temporales con marcas de tiempo para asegurar unicidad en SQLite
        timestamp_now = int(datetime.utcnow().timestamp())
        redemption_id = f"red_{timestamp_now}"
        loyalty_tx_id = f"lt_{timestamp_now}"

        # 4. Insertar el cupón físico en la tabla 'reward_redemptions' en estado 'pending' (por usar)
        new_redemption = RewardRedemption(
            id_reward_redemption=redemption_id,
            user_id=user.id_user,
            reward_id=reward.id_reward,
            reservation_id=reservation_id,
            stars_spent=costo_premio,
            status="pending",
            created_at=datetime.utcnow()
        )
        session.add(new_redemption)

        # 5. Insertar la auditoría contable en la tabla 'loyalty_transactions'
        new_txn = LoyaltyTransaction(
            id_loyalty_transaction=loyalty_tx_id,
            user_id=user.id_user,
            reservation_id=reservation_id,
            reward_redemption_id=redemption_id,
            type="spent",
            stars=costo_premio,
            description=f"Canje del premio: {reward.name}",
            created_at=datetime.utcnow()
        )
        session.add(new_txn)

        # Confirmación de la transacción atómica
        session.commit()

        # Cadena estructurada idéntica para pintar el código QR de validación física en Dart/Flutter
        qr_string = f"hotelya.reward.redeem_{redemption_id}_user_{user.id_user}"

        return jsonify({
            'message': 'Canje procesado con éxito. Presenta tu código QR en el hotel.',
            'data': {
                'id': new_redemption.id_reward_redemption,
                'stars_spent': int(new_redemption.stars_spent),
                'status': new_redemption.status,
                'qr_validation_string': qr_string,

                'stars_remaining': int(user.stars_available), # <-- Envía las estrellas que le quedan al usuario
                'reward': {                                   # <-- Envía qué fue lo que compró exactamente
                    'id': reward.id_reward,
                    'name': reward.name,
                    'description': reward.description if reward.description else '',
                    'type': reward.type if reward.type else 'General'
                }
            },
            'success': True, 
            'error': None
        }), 201

    except Exception as e:
        session.rollback()  # Revierte todo el canje si hay un error de escritura (evita pérdida de estrellas)
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error transaccional al procesar el canje',
            'data': None, 
            'success': False, 
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/loyalty/history', methods=['GET'])
@jwt_required()
def get_loyalty_history():
    """
    Historial de cuenta para la UI de Flutter (/history).
    Muestra el detalle contable de todas las estrellas ganadas y gastadas por el usuario.
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
        tx_list = []
        for t in transactions:
            # 💡 Control preventivo de tipos para las fechas provenientes de SQLite
            if isinstance(t.created_at, datetime):
                fecha_str = t.created_at.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(t.created_at, str):
                fecha_str = t.created_at
            else:
                fecha_str = ''

            tx_list.append({
                'id': t.id_loyalty_transaction,
                'reservation_id': t.reservation_id,
                'reward_redemption_id': t.reward_redemption_id,
                'type': t.type,  # 'earned' o 'spent'
                'stars': int(t.stars),
                'description': t.description if t.description else '',
                'created_at': fecha_str
            })
        return jsonify({
            'message': 'Historial de transacciones de lealtad obtenido correctamente',
            'data': tx_list,
            'success': True, 
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al consultar el historial de lealtad',
            'data': None, 
            'success': False, 
            'error': str(e)
        }), 500
    finally:
        session.close()