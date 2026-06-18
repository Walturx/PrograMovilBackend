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
        # Validar si el estado de la sesión existe y es afirmativo (sea booleano o string 'True')
        status = session.get('status')
        if status and (status == True or status == 'True'):
            return fn(*args, **kwargs)
        
        # Si no está logueado o es falso, directo al error 403
        return redirect('/error/403')
    return _only_logged

def logged_go_admin(fn):
    @wraps(fn)
    def _logged_go_admin(*args, **kwargs):
        status = session.get('status')
        # Si ya está logueado, lo redirigimos al panel de administración
        if status and (status == True or status == 'True'):
            return redirect('/admin')
            
        # Corregido: Se eliminó la doble ejecución de fn()
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
            # Verifica de manera nativa que el token JWT venga en los headers o cookies
            verify_jwt_in_request()
            
            # Obtenemos el ID del usuario (que guardamos en 'identity' durante el sign-in)
            user_id = get_jwt_identity()

            if not user_id:
                return jsonify({
                    "message": "Token inválido",
                    "data": None,
                    "success": False,
                    "error": "Missing user identity"
                }), 401
                
            # Almacenamos los datos en el objeto global 'g' para usarlos cómodamente en las rutas
            g.user_id = user_id
            g.username = user_id  # O el campo que uses como identificador principal

            return fn(*args, **kwargs)

        except Exception as e:
            return jsonify({
                "message": "Token inválido o expirado",
                "data": None,
                "success": False,
                "error": str(e)
            }), 401

    return wrapper