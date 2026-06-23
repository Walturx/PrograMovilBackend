from datetime import timedelta
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from flask import Blueprint, request, make_response, session, jsonify
from main.database import Session
from main.application import REVOKED_TOKENS
from main.models import User

api = Blueprint('main_apis', __name__)

@api.route('/api/sign-in', methods=["POST"])
def sign_in():
  data = request.get_json()
  username = data['username']
  password = data['password']
  
  db_session = Session()
  user = db_session.query(User).filter(
    User.user_name == username,
    User.password == password
  ).first()
  
  if user:
    expires = timedelta(minutes=300)
    access_token = create_access_token(identity=username, expires_delta=expires)
    response = make_response()
    response.set_cookie('access_token', access_token, max_age=30, httponly=True)
    session['status'] = 'True'
    session['user'] = user.to_dict()
    return jsonify({"message": access_token}), 200
  else:
    return jsonify({"error": "Usuario y contraseña incorrectos"}), 404

@api.route('/api/sign-out', methods=['GET'])
@jwt_required()
def signout():
  jti = get_jwt()["jti"]
  REVOKED_TOKENS.append(jti)
  session.clear()
  return jsonify({"message": "Sesión cerrada correctamente"}), 200

@api.route('/api/comments', methods=['GET'])
def comments():
  comments_list = [
    {
      'guest': 'Juan Pérez',
      'date': '10 de julio, 2023',
      'comment': 'Un lugar maravilloso para visitar con la familia. ¡Las vistas son impresionantes y el personal muy amable!'
    },
    {
      'guest': 'Ana Gómez',
      'date': '15 de julio, 2023',
      'comment': '¡Absolutamente recomendado! Un excelente lugar para desconectar y disfrutar de la naturaleza.'
    }
  ]
  return jsonify(comments_list), 200