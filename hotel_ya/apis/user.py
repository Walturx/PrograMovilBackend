# hotel_ya\apis\user.py
import traceback
from datetime import timedelta, datetime
from flask import Blueprint, jsonify, request
from main.database import Session
from main.models import User
from flask_jwt_extended import create_access_token, jwt_required

api = Blueprint('hotel_ya_apis_users', __name__)

@api.route('/apis/v1/users/validate-token', methods=['GET'])
@jwt_required()
def validate_token():
    """
    Endpoint utilizado por la SplashScreen ('/') para verificar en segundo plano
    si el token almacenado localmente en el celular sigue activo y vigente.
    """
    return jsonify({
        'message': 'Token válido y activo',
        'data': {'valid': True},
        'success': True,
        'error': None
    }), 200


@api.route('/apis/v1/users/login', methods=['POST'])
def login():
    """
    Endpoint para la pantalla '/login'. Valida las credenciales (email y password)
    y retorna el token JWT junto con el diccionario del usuario.
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'message': 'Debe enviar un JSON válido',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({
            'message': 'email y password son obligatorios',
            'data': None,
            'success': False,
            'error': 'Missing required fields'
        }), 400

    session = Session()

    try:
        # Búsqueda basada en el modelo unificado del diagrama PlantUML
        user = (
            session.query(User)
            .filter(
                User.email == email,
                User.password_hash == password
            )
            .first()
        )

        if not user:
            return jsonify({
                'message': 'Usuario o contraseña incorrectos',
                'data': None,
                'success': False,
                'error': 'Unauthorized'
            }), 401

        # Generamos el token dinámico con 30 días de duración
        expires = timedelta(days=30)
        jwt = create_access_token(
            identity=str(user.id),
            expires_delta=expires,
            additional_claims={
                "user_id": user.id
            }
        )

        return jsonify({
            'message': 'Login exitoso',
            'data': {
                'user': user.to_dict(),  # Entrega la estructura exacta sincronizada con Flutter
                'jwt': jwt
            },
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error durante el login',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500

    finally:
        session.close()


@api.route('/apis/v1/users/register', methods=['POST'])
def register_user():
    """
    Permite la creación de nuevas cuentas de usuario directo desde la App móvil.
    """
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data or 'name' not in data:
        return jsonify({
            'message': 'Faltan campos requeridos (email, password y name)',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400

    session = Session()
    try:
        # Verificar si el correo ya existe
        existing_user = session.query(User).filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'message': 'El correo electrónico ya se encuentra registrado.',
                'data': None,
                'success': False,
                'error': 'Conflict'
            }), 400

        # Crear nueva instancia siguiendo la estructura del diagrama PlantUML y UserModel de Dart
        new_user = User(
            id=f"usr_{int(datetime.utcnow().timestamp())}",
            email=data['email'],
            password_hash=data['password'],
            name=data['name'],
            lastname=data.get('lastname', ''),
            phone=data.get('phone', ''),
            document_type=data.get('document_type', ''),
            document_number=data.get('document_number', ''),
            avatar_url=data.get('avatar_url', ''),
            nationality=data.get('nationality', ''),
            stars_available=0  # Comienza con cero puntos de fidelidad
        )
        
        session.add(new_user)
        session.commit()

        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'data': new_user.to_dict(),
            'success': True,
            'error': None
        }), 201

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error al registrar el usuario',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/users/forgot-password', methods=['POST'])
def forgot_password():
    """
    Endpoint para la pantalla '/forgot_password'. Simula de forma estructurada
    la petición de recuperación de contraseña.
    """
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({
            'message': 'El campo email es obligatorio',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400
        
    return jsonify({
        'message': 'Se ha enviado exitosamente un enlace de restauración a tu correo',
        'data': None,
        'success': True,
        'error': None
    }), 200