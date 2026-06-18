# hotel_ya\apis\auth.py
import traceback
from datetime import timedelta, datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from main.database import Session
from main.models import User
from main.application import REVOKED_TOKENS

api = Blueprint('hotel_ya_apis_auth', __name__)

@api.route('/apis/v1/auth/validate-token', methods=['GET'])
@jwt_required()
def validate_token():
    """
    Verifica en tiempo real desde Flutter si el token JWT almacenado localmente
    sigue siendo válido y no ha sido revocado.
    """
    return jsonify({
        'message': 'Token válido y activo',
        'data': {'valid': True},
        'success': True,
        'error': None
    }), 200


@api.route('/apis/v1/auth/login', methods=['POST'])
def login():
    """
    Módulo de inicio de sesión. Compara las credenciales y genera un token JWT
    con una duración extendida de 30 días ideal para entornos móviles.
    """
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'message': 'Email y password son requeridos',
            'data': None, 'success': False, 'error': 'Bad Request'
        }), 400

    session = Session()
    try:
        user = session.query(User).filter(
            User.email == data['email'],
            User.password_hash == data['password'] # Mapeado directo según tu persistencia actual
        ).first()

        if not user:
            return jsonify({
                'message': 'Correo o contraseña incorrectos',
                'data': None, 'success': False, 'error': 'Unauthorized'
            }), 401

        # CORRECCIÓN: Definición e inyección correcta del tiempo de expiración
        expires = timedelta(days=30)
        jwt = create_access_token(
            identity=str(user.id), 
            expires_delta=expires,
            additional_claims={"user_id": user.id}
        )

        return jsonify({
            'message': 'Login exitoso',
            'data': {
                'user': user.to_dict(), # Retorna el perfil completo estructurado para Flutter
                'jwt': jwt
            },
            'success': True, 'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al iniciar sesión', 
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/auth/register', methods=['POST'])
def register_user():
    """
    Registra nuevos usuarios asegurando que el correo no esté duplicado
    e inicializa su contador de estrellas de fidelidad en 0.
    """
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'message': 'Faltan datos obligatorios', 
            'data': None, 'success': False, 'error': 'Bad Request'
        }), 400

    session = Session()
    try:
        if session.query(User).filter_by(email=data['email']).first():
            return jsonify({
                'message': 'El correo ya está registrado', 
                'data': None, 'success': False, 'error': 'Conflict'
            }), 400

        new_user = User(
            id=f"usr_{int(datetime.utcnow().timestamp())}", # ID seguro en formato String
            email=data['email'],
            password_hash=data['password'],
            name=data.get('name', ''),
            lastname=data.get('lastname', ''),
            stars_available=0
        )
        session.add(new_user)
        session.commit()
        
        return jsonify({
            'message': 'Usuario registrado con éxito', 
            'data': {'id': new_user.id, 'email': new_user.email}, 
            'success': True, 'error': None
        }), 201
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Error al registrar usuario', 
            'data': None, 'success': False, 'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    Simula la solicitud de recuperación de contraseña enviando una confirmación.
    """
    return jsonify({
        'message': 'Enlace de recuperación enviado exitosamente a tu correo',
        'data': None, 'success': True, 'error': None
    }), 200


@api.route('/apis/v1/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Revoca de forma inmediata el token de acceso actual del cliente.
    """
    try:
        jti = get_jwt()["jti"]
        REVOKED_TOKENS.append(jti)
        return jsonify({
            'message': 'Sesión cerrada correctamente', 
            'data': None, 'success': True, 'error': None
        }), 200
    except Exception as e:
        return jsonify({
            'message': 'Error al cerrar sesión', 
            'data': None, 'success': False, 'error': str(e)
        }), 500