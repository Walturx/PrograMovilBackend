from datetime import timedelta
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from flask import Blueprint, request, make_response, session, jsonify
from main.database import Session
from main.application import REVOKED_TOKENS
from main.models import User, Hotel  # Importamos tus modelos reales de hoteles

api = Blueprint('main_apis', __name__)

@api.route('/api/sign-in', methods=["POST"])
def sign_in():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password') # En desarrollo comparas directo o aplicando tu lógica de hash
    
    db_session = Session()
    # Corregido: Filtra por email y password_hash mapeando tu base de datos de hoteles
    user = db_session.query(User).filter(
        User.email == email,
        User.password_hash == password
    ).first()
    
    if user:
        expires = timedelta(minutes=300) 
        # Modificado: Se usa el ID del usuario como identidad para que tus decoradores JWT lo lean bien
        access_token = create_access_token(identity=user.id, expires_delta=expires)
        
        response = make_response(jsonify({"message": access_token, "user": user.to_dict()}), 200)
        # Corregido: max_age cambiado a 300 segundos (5 minutos) o el equivalente a la duración de tu token
        response.set_cookie('access_token', access_token, max_age=300, httponly=True)
        
        session['status'] = 'True'
        session['user'] = user.to_dict()
        return response
    else:
        return jsonify({"error": "Correo o contraseña incorrectos"}), 404

@api.route('/api/sign-out', methods=['GET'])
@jwt_required()
def signout():
    jti = get_jwt()["jti"]
    REVOKED_TOKENS.append(jti)
    session.clear()
    return jsonify({"message": "Sesión cerrada correctamente"}), 200

# Reemplazado /api/comments por una API útil para tu catálogo
@api.route('/api/main-hotels', methods=['GET'])
def get_main_hotels():
    db_session = Session()
    hotels = db_session.query(Hotel).filter(Hotel.is_active == True).limit(3).all()
    return jsonify([hotel.to_dict() for hotel in hotels]), 200

@api.route('/api/v1/demo')
def demo():
    return '<h1>Bienvenido a la API de Hotel_Ya v3</h1>'

@api.route('/api/sign-up', methods=["POST"])
def sign_up():
    data = request.get_json()
    
    # Extraer los campos enviados desde tu cliente HTTP
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    lastname = data.get('lastname')
    phone = data.get('phone')
    document_type = data.get('document_type')
    document_number = data.get('document_number')

    if not email or not password:
        return jsonify({"error": "Email y contraseña son obligatorios"}), 400

    db_session = Session()

    # Verificar si el usuario ya existe para evitar duplicados
    existing_user = db_session.query(User).filter(User.email == email).first()
    if existing_user:
        return jsonify({"error": "El correo ya está registrado"}), 400

    # Generar un ID único simple (puedes usar un contador o un UUID breve)
    # Contamos los usuarios actuales y le sumamos 1 para mantener tu formato 'u1', 'u2', etc.
    user_count = db_session.query(User).count()
    new_id = f"u{user_count + 1}"

    # Crear la instancia del nuevo usuario
    new_user = User(
        id=new_id,
        email=email,
        password_hash=password,  # En desarrollo se guarda directo según tu estructura
        name=name,
        lastname=lastname,
        phone=phone,
        document_type=document_type,
        document_number=document_number,
        avatar_url="https://i.pravatar.cc/300", # Un avatar por defecto genérico
        nationality="Peruano",
        stars_available=0
    )

    try:
        db_session.add(new_user)
        db_session.commit()  # Guardar cambios de verdad en la BD
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "user": new_user.to_dict()
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": f"No se pudo crear el usuario: {str(e)}"}), 500
    

from sqlalchemy import or_
from main.models import Room, Amenity  # Asegúrate de importar Room y Amenity arriba

# 1. Obtener Lista de todos los Hoteles Activos
@api.route('/api/hotels', methods=['GET'])
def get_all_hotels():
    db_session = Session()
    hotels = db_session.query(Hotel).filter(Hotel.is_active == True).all()
    return jsonify([hotel.to_dict() for hotel in hotels]), 200

# 2. Buscar Hoteles por término (Nombre o Descripción)
@api.route('/api/hotels/search', methods=['GET'])
def search_hotels():
    query_param = request.args.get('query', '')
    if not query_param:
        return jsonify({"error": "Falta el parámetro 'query'"}), 400
        
    db_session = Session()
    # Busca coincidencias parciales en nombre o descripción (Case Insensitive)
    search_filter = or_(
        Hotel.name.ilike(f"%{query_param}%"),
        Hotel.description.ilike(f"%{query_param}%")
    )
    hotels = db_session.query(Hotel).filter(Hotel.is_active == True, search_filter).all()
    return jsonify([hotel.to_dict() for hotel in hotels]), 200

# 3. Obtener Detalle de un Hotel específico
@api.route('/api/hotels/<string:hotel_id>', methods=['GET'])
def get_hotel_detail(hotel_id):
    db_session = Session()
    hotel = db_session.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        return jsonify({"error": "Hotel no encontrado"}), 404
    return jsonify(hotel.to_dict()), 200

# 4. Obtener las Comodidades (Amenities) del Hotel
@api.route('/api/hotels/<string:hotel_id>/amenities', methods=['GET'])
def get_hotel_amenities(hotel_id):
    db_session = Session()
    hotel = db_session.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        return jsonify({"error": "Hotel no encontrado"}), 404
    
    # Gracias a que arreglamos la relación ManyToMany, puedes acceder directo:
    return jsonify([amenity.to_dict() for amenity in hotel.amenities]), 200

# 5. Obtener Habitaciones disponibles del Hotel
@api.route('/api/hotels/<string:hotel_id>/rooms', methods=['GET'])
def get_hotel_rooms(hotel_id):
    db_session = Session()
    rooms = db_session.query(Room).filter(
        Room.hotel_id == hotel_id, 
        Room.is_available == True
    ).all()
    return jsonify([room.to_dict() for room in rooms]), 200