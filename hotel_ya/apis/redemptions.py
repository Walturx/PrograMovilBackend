# hotel_ya\apis\redemptions.py
import traceback
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import RewardRedemption
from sqlalchemy.orm import joinedload

api = Blueprint('hotel_ya_apis_redemptions', __name__)

@api.route('/apis/v1/users/me/redemptions', methods=['GET'])
@jwt_required()
def get_redemption_history():
    """
    Retorna el historial de premios canjeados por el usuario (cupones QR).
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        # Usamos joinedload para pre-cargar la relación con Reward eficientemente
        redemptions = (
            session.query(RewardRedemption)
            .options(joinedload(RewardRedemption.reward))
            .filter(RewardRedemption.user_id == str(user_id))
            .order_by(RewardRedemption.created_at.desc())
            .all()
        )
        
        return jsonify({
            'message': 'Historial de beneficios canjeados obtenido',
            'data': [r.to_dict() for r in redemptions],
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al cargar el historial de premios',
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()