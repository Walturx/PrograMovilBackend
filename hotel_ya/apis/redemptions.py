# ==============================================================================
# ARCHIVO: hotel_ya/apis/redemptions.py
# PROPÓSITO: Este módulo define los endpoints para la consulta y control del
#            historial de recompensas canjeadas por el usuario. Permite alimentar
#            la "billetera de cupones" en Flutter, exponiendo el estado físico
#            de cada premio (pendiente/usado) y optimizando con lazy/joinedload.
# ==============================================================================

import traceback
from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import RewardRedemption
from sqlalchemy.orm import joinedload

# Creación del Blueprint para registrar el módulo de redenciones en Flask
api = Blueprint('hotel_ya_apis_redemptions', __name__)

@api.route('/apis/v1/loyalty/redemptions', methods=['GET'])
@jwt_required()
def get_user_redemptions():
    """
    Endpoint para la Billetera de Cupones/Premios Canjeados.

    GET /apis/v1/loyalty/redemptions
    Obtiene la lista completa de premios reclamados por el usuario autenticado,
    permitiendo a Flutter separar visualmente los cupones listos para usar (pending)
    de los ya consumidos (used).
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        # Usamos joinedload para pre-cargar la relación del premio (Reward) y mitigar consultas N+1
        redemptions = (
            session.query(RewardRedemption)
            .options(joinedload(RewardRedemption.reward))
            .filter(RewardRedemption.user_id == str(user_id))
            .order_by(RewardRedemption.created_at.desc())
            .all()
        )

        data_response = []
        for r in redemptions:
            # Re-generamos la cadena idéntica del QR para que Flutter la pinte en la billetera de forma consistente
            qr_string = f"hotelya.reward.redeem_{r.id_reward_redemption}_user_{user_id}"

            # 💡 Control de tipos preventivo para el formateo de fechas de SQLite
            if isinstance(r.created_at, datetime):
                fecha_str = r.created_at.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(r.created_at, str):
                fecha_str = r.created_at
            else:
                fecha_str = ''

            data_response.append({
                'id': r.id_reward_redemption,
                'stars_spent': int(r.stars_spent) if r.stars_spent else 0,
                'status': r.status if r.status else 'pending',  # 'pending' o 'used'
                'created_at': fecha_str,
                'qr_validation_string': qr_string,
                'reward': {
                    'id': r.reward.id_reward if r.reward else None,
                    'name': r.reward.name if r.reward else 'Premio Reclamado',
                    'description': r.reward.description if (r.reward and r.reward.description) else ''
                }
            })

        return jsonify({
            'message': 'Lista de premios canjeados obtenida con éxito',
            'data': data_response,
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al compilar el listado de redenciones del usuario',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()