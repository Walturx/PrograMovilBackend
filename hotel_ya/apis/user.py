# ==============================================================================
# ARCHIVO: hotel_ya/apis/user.py
# PROPÓSITO: Este módulo define los endpoints de la API de Flask relacionados con
#            el ciclo de vida del usuario (Autenticación, Registro, Perfil, 
#            Recuperación y Logout) adaptados para la app de Flutter.
#            Actúa como capa de validación de seguridad e identidad utilizando JWT
#            y transformando las propiedades relacionales de la BD (UML: id_user)
#            en contratos limpios y seguros para los modelos en el Front-End.
# ==============================================================================

import random
import traceback
from datetime import timedelta, datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from main.database import Session
from main.models import User
from main.application import REVOKED_TOKENS  # Lista negra global para la revocación de tokens

# Creación del Blueprint para registrar el módulo de gestión de usuarios en Flask
api = Blueprint('hotel_ya_apis_users', __name__)

@api.route('/apis/v1/users/validate-token', methods=['GET'])
@jwt_required()
def validate_token():
    """
    Endpoint para Validación de Token.

    GET /apis/v1/users/validate-token
    Verifica en tiempo real desde los interceptores de Flutter si el token JWT 
    almacenado localmente en el dispositivo sigue siendo válido y no ha expirado.
    """
    user_id = get_jwt_identity()
    return jsonify({
        'message': 'Token activo y verificado correctamente',
        'data': {'user_id': user_id},
        'success': True,
        'error': None
    }), 200


@api.route('/apis/v1/users/login', methods=['POST'])
def login():
    """
    Endpoint para Inicio de Sesión.

    POST /apis/v1/users/login
    """
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            'message': 'El correo electrónico y la contraseña son obligatorios',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400

    email = data.get('email').strip().lower()
    password = data.get('password')

    session = Session()
    try:
        user = session.query(User).filter(User.email == email).first()

        if not user or user.password_hash != password:  # Sincronizado con password_hash del UML
            return jsonify({
                'message': 'Credenciales de acceso incorrectas',
                'data': None,
                'success': False,
                'error': 'Unauthorized'
            }), 401

        # Access token de vida corta (usa el JWT_ACCESS_TOKEN_EXPIRES global = 30 min)
        access_token = create_access_token(identity=str(user.id_user))
        # Refresh token de vida larga (30 días); solo sirve para pedir nuevos access tokens
        refresh_token = create_refresh_token(identity=str(user.id_user))

        # 💡 MODIFICACIÓN: Obtener estrellas disponibles de forma segura para mapearlo en la sesión iniciada
        stars = int(getattr(user, 'stars_available', 0) or 0)

        return jsonify({
            'message': 'Autenticación exitosa',
            'data': {
                'token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id_user,
                    'email': user.email,
                    'name': user.name,
                    'lastname': user.lastname if user.lastname else '',
                    'phone': user.phone if user.phone else '',
                    'birthdate': user.birthdate if user.birthdate else '',
                    'document_type': user.document_type if user.document_type else '',
                    'document_number': user.document_number if user.document_number else '',
                    'nationality': user.nationality if user.nationality else '',
                    'stars_available': stars  # <-- Se añadió aquí
                }
            },
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error interno durante el proceso de login',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/users/register', methods=['POST'])
def register_user():
    """
    Endpoint para Registro de Nuevos Usuarios.

    POST /apis/v1/users/register
    """
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data or 'name' not in data:
        return jsonify({
            'message': 'Los campos email, password y name son obligatorios',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400

    email = data.get('email').strip().lower()
    session = Session()
    try:
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            return jsonify({
                'message': 'El correo electrónico ya se encuentra registrado',
                'data': None,
                'success': False,
                'error': 'Conflict'
            }), 409

        user_id = f"usr_{int(datetime.utcnow().timestamp())}"

        # 💡 MODIFICACIÓN: Lee el JSON enviado de Flutter, si no viene el campo usa 120 por defecto.
        initial_stars = int(data.get('stars_available', 120))

        # Edad opcional: si viene un valor numérico lo guardamos, si no queda en None.
        age_raw = data.get('age')
        age = int(age_raw) if age_raw not in (None, '') else None

        new_user = User(
            id_user=user_id,
            email=email,
            password_hash=data.get('password'),  # Sincronizado con password_hash de los modelos
            name=data.get('name'),
            lastname=data.get('lastname', ''),
            phone=data.get('phone', ''),
            birthdate=data.get('birthdate', ''),         # Fecha de nacimiento del formulario de registro
            age=age,
            document_type=data.get('document_type', ''),
            document_number=data.get('document_number', ''),
            nationality=data.get('nationality', ''),
            avatar_url='https://images.unsplash.com/photo-1535713875002-d1d0cf377fde',
            stars_available=initial_stars  # <-- Se asignan las estrellas aquí
        )

        session.add(new_user)
        session.commit()

        access_token = create_access_token(identity=str(new_user.id_user), expires_delta=timedelta(days=7))

        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'data': {
                'token': access_token,
                'user': {
                    'id': new_user.id_user,
                    'email': new_user.email,
                    'name': new_user.name,
                    'lastname': new_user.lastname if new_user.lastname else '',
                    'phone': new_user.phone if new_user.phone else '',
                    'birthdate': new_user.birthdate if new_user.birthdate else '',
                    'document_type': new_user.document_type if new_user.document_type else '',
                    'document_number': new_user.document_number if new_user.document_number else '',
                    'nationality': new_user.nationality if new_user.nationality else '',
                    'stars_available': new_user.stars_available  # <-- Se añadió aquí para la respuesta de Flutter
                }
            },
            'success': True,
            'error': None
        }), 201
    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error al procesar el registro',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/users/forgot-password', methods=['POST'])
def forgot_password():
    """
    Endpoint para Recuperación de Contraseñas.

    POST /apis/v1/users/forgot-password
    """
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({
            'message': 'El correo electrónico es un campo obligatorio',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400

    email = data.get('email').strip().lower()
    session = Session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            # Respuesta neutra: no revelamos si el correo existe o no (buena práctica de seguridad)
            return jsonify({
                'message': 'Si el correo electrónico existe en nuestros registros, recibirá un mensaje a la brevedad',
                'data': None,
                'success': True,
                'error': None
            }), 200

        # Generamos un código de 6 dígitos y lo persistimos en la BD (columna reset_password_token)
        token = random.randint(100000, 999999)
        user.reset_password_token = token
        session.commit()

        # NOTA: en producción este código se enviaría por correo. Aquí lo devolvemos
        # en la respuesta para poder probar el flujo de reset desde REST Client.
        return jsonify({
            'message': 'Se ha enviado un enlace de restauración al correo proporcionado',
            'data': {'email': email, 'reset_token': token},
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al procesar la solicitud de recuperación',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/users/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Endpoint para Cierre de Sesión (Invalidación de Token).

    POST /apis/v1/users/logout
    """
    try:
        jti = get_jwt()['jti']
        
        # CAMBIA .add(jti) POR .append(jti) PARA ACUMULAR EN LA LISTA
        REVOKED_TOKENS.append(jti)
        
        return jsonify({
            'message': 'Sesión cerrada correctamente. Token revocado con éxito.',
            'data': None,
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        return jsonify({
            'message': 'Error al procesar el cierre de sesión',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500


@api.route('/apis/v1/users/me', methods=['GET'])
@jwt_required()
def get_current_user_profile():
    """
    Endpoint de Perfil para Flutter (/profile).

    GET /apis/v1/users/me
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        user = session.query(User).filter(User.id_user == str(user_id)).first()
        if not user:
            return jsonify({
                'message': 'No se encontró el registro del usuario',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404

        stars_available = getattr(user, 'stars_available', 0) or 0

        return jsonify({
            'message': 'Perfil de usuario cargado con éxito',
            'data': {
                'id': user.id_user,
                'email': user.email,
                'name': user.name,
                'lastname': user.lastname if user.lastname else '',
                'phone': user.phone if user.phone else '',
                'birthdate': user.birthdate if user.birthdate else '',
                'document_type': user.document_type if user.document_type else '',
                'document_number': user.document_number if user.document_number else '',
                'avatar_url': user.avatar_url if user.avatar_url else 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde',
                'nationality': user.nationality if user.nationality else '',
                'stars_available': int(stars_available)
            },
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error al obtener los detalles del perfil',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/users/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """
    Endpoint para Editar la Información del Perfil.

    PUT /apis/v1/users/profile
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        req_data = request.get_json() or {}
        
        user = session.query(User).filter(User.id_user == str(user_id)).first()
        if not user:
            return jsonify({
                'message': 'No se encontró el registro del usuario',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404

        if 'name' in req_data:
            user.name = req_data['name']
        if 'lastname' in req_data:
            user.lastname = req_data['lastname']
        if 'phone' in req_data:
            user.phone = req_data['phone']
        if 'birthdate' in req_data:
            user.birthdate = req_data['birthdate']
        if 'document_type' in req_data:
            user.document_type = req_data['document_type']
        if 'document_number' in req_data:
            user.document_number = req_data['document_number']
        if 'nationality' in req_data:
            user.nationality = req_data['nationality']
        if 'avatar_url' in req_data:
            user.avatar_url = req_data['avatar_url']

        session.commit()

        return jsonify({
            'message': 'Perfil actualizado con éxito',
            'data': {
                'id': user.id_user,
                'email': user.email,
                'name': user.name,
                'lastname': user.lastname if user.lastname else '',
                'phone': user.phone if user.phone else '',
                'birthdate': user.birthdate if user.birthdate else '',
                'document_type': user.document_type if user.document_type else '',
                'document_number': user.document_number if user.document_number else '',
                'avatar_url': user.avatar_url if user.avatar_url else 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde',
                'nationality': user.nationality if user.nationality else '',
                'stars_available': int(getattr(user, 'stars_available', 0) or 0)
            },
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Error al actualizar la información del perfil',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/users/reset-password', methods=['POST'])
def reset_password():
    """
    Endpoint para Restablecer la Contraseña.

    POST /apis/v1/users/reset-password
    Recibe el correo, el código enviado por 'forgot-password' y la nueva contraseña.
    Valida que el código coincida con el guardado en la BD y actualiza la clave.

    Body JSON:
        { "email": "...", "token": 123456, "new_password": "..." }
    """
    data = request.get_json() or {}
    if not all(k in data for k in ('email', 'token', 'new_password')):
        return jsonify({
            'message': 'email, token y new_password son obligatorios',
            'data': None,
            'success': False,
            'error': 'Bad Request'
        }), 400

    email = data.get('email').strip().lower()
    session = Session()
    try:
        user = session.query(User).filter(User.email == email).first()

        # Validamos usuario, que exista un token pendiente y que coincida con el enviado
        if not user or not user.reset_password_token or str(user.reset_password_token) != str(data.get('token')):
            return jsonify({
                'message': 'El código de recuperación es inválido o ha expirado',
                'data': None,
                'success': False,
                'error': 'Unauthorized'
            }), 401

        # Actualizamos la contraseña (esquema actual: se compara password_hash directo en login)
        user.password_hash = data.get('new_password')
        # Invalidamos el token para que no pueda reutilizarse
        user.reset_password_token = None
        session.commit()

        return jsonify({
            'message': 'Contraseña restablecida correctamente',
            'data': {'email': email},
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        session.rollback()
        traceback.print_exc()
        return jsonify({
            'message': 'Error al restablecer la contraseña',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api.route('/apis/v1/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_access_token():
    """
    Endpoint para Renovar el Access Token.

    POST /apis/v1/auth/refresh
    Requiere enviar el REFRESH token (no el de acceso) en el header:
        Authorization: Bearer <refresh_token>
    Devuelve un access token nuevo sin pedir credenciales otra vez.
    """
    try:
        identity = get_jwt_identity()  # id_user embebido en el refresh token
        new_access_token = create_access_token(identity=identity)

        return jsonify({
            'message': 'Token renovado correctamente',
            'data': {'token': new_access_token},
            'success': True,
            'error': None
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Error al renovar el token',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500