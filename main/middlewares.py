from functools import wraps
from flask import session, redirect, request, jsonify, g
from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt,
    get_jwt_identity
)

def only_logged(fn):
  @wraps(fn)
  def _only_logged(*args, **kwargs):
    if session.get('status'):
      if session.get('status') == False:
        return redirect('/error/403')
    else:
      return redirect('/error/403')
    return fn(*args, **kwargs)
  return _only_logged

def logged_go_admin(fn):
  @wraps(fn)
  def _logged_go_admin(*args, **kwargs):
    if session.get('status'):
      if session.get('status') == True:
        return redirect('/admin')
      else:
        fn(*args, **kwargs)
    else:
      fn(*args, **kwargs)
    return fn(*args, **kwargs)
  return _logged_go_admin

def not_found(e):
  if request.method == 'GET':
    extensions_to_check = ['.css', '.js', '.woff', 'png']
    if any(ext in request.url for ext in extensions_to_check):
      return 'Recurso no encontrado', 404
    else:
      return redirect('/error/404')
  else:
    return 'Recurso no encontrado', 404

def jwt_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    try:
      verify_jwt_in_request()
      claims = get_jwt()

      if not claims.get("user_id"):
        return jsonify({
          "message": "Token inválido",
          "data": None,
          "success": False,
          "error": "Missing user_id claim"
        }), 401
        
      g.user_id = claims.get("user_id")
      g.username = get_jwt_identity()

      return fn(*args, **kwargs)

    except Exception as e:
      return jsonify({
        "message": "Token inválido o expirado",
        "data": None,
        "success": False,
        "error": str(e)
      }), 401

  return wrapper