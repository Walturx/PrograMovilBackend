# ==============================================================================
# ARCHIVO: hotel_ya/apis/notifications.py
# PROPÓSITO: Este módulo define los endpoints de la API de Flask responsables de
#            la bandeja de entrada y control de lectura de notificaciones para
#            los usuarios de la aplicación móvil de Flutter.
#            Implementa un esquema desacoplado mediante un JOIN tradicional
#            entre la alerta base y el estado físico relacional de cada usuario.
# ==============================================================================

import traceback
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from main.database import Session
from main.models import Notification, UserNotification

# Creación del Blueprint para registrar el módulo de notificaciones en Flask
api = Blueprint('hotel_ya_apis_notifications', __name__)

@api.route('/apis/v1/notifications', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """
    Endpoint para la Bandeja de Entrada de Notificaciones.

    GET /apis/v1/notifications
    Obtiene el listado completo de alertas y mensajes promocionales o de reserva
    dirigidos al usuario autenticado, ordenados desde la más reciente.

    ---
    Cabeceras Requeridas (Headers):
        - Authorization: Bearer <JWT_TOKEN>

    Estructura del JSON de Retorno con Éxito (Status 200):
        {
            "success": true,
            "message": "Bandeja de notificaciones cargada correctamente",
            "error": null,
            "data": [
                {
                    "id": "string",
                    "title": "string",
                    "body": "string",
                    "type": "info"|"alert"|"promo",
                    "is_read": bool,
                    "created_at": "YYYY-MM-DD HH:MM:SS"
                }
            ]
        }
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        # Hacemos un JOIN entre la tabla asociativa y la notificación base
        results = (
            session.query(Notification, UserNotification)
            .join(UserNotification, Notification.id_notification == UserNotification.notification_id)
            .filter(UserNotification.user_id == str(user_id))
            .order_by(Notification.created_at.desc())
            .all()
        )

        notifications_list = []
        for notification, user_node in results:
            # Control seguro de tipo para fechas provenientes de motores SQLite/SQL
            if isinstance(notification.created_at, datetime):
                fecha_str = notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(notification.created_at, str):
                fecha_str = notification.created_at
            else:
                fecha_str = ''

            notifications_list.append({
                'id': notification.id_notification,
                'title': notification.title,
                'body': notification.body,
                'type': notification.type if notification.type else 'info',  # 'info', 'alert', 'promo'
                'is_read': bool(user_node.is_read),                          # Estado de lectura físico del UML
                'created_at': fecha_str
            })

        return jsonify({
            'message': 'Bandeja de notificaciones cargada correctamente',
            'data': notifications_list,
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'message': 'Ocurrió un error interno al consultar las notificaciones',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        # Bloque crítico: Cierre de seguridad de la sesión para liberar el pool de conexiones
        session.close()


@api.route('/apis/v1/notifications/<string:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(notification_id):
    """
    Endpoint para Cambiar Estado de Lectura.

    POST /apis/v1/notifications/<notification_id>/read
    Marca una notificación específica como leída (actualiza 'is_read' a True en el UML)
    restringiendo la mutación atómicamente al usuario autenticado.
    """
    user_id = get_jwt_identity()
    session = Session()
    try:
        # 💡 Búsqueda estricta combinada para garantizar que un usuario no altere registros ajenos
        user_node = (
            session.query(UserNotification)
            .filter(
                UserNotification.notification_id == notification_id,
                UserNotification.user_id == str(user_id)
            )
            .first()
        )

        if not user_node:
            return jsonify({
                'message': 'No se encontró la notificación solicitada para este usuario',
                'data': None,
                'success': False,
                'error': 'Not Found'
            }), 404

        # Modificación atómica del estado de lectura
        user_node.is_read = True
        session.commit()

        return jsonify({
            'message': 'Notificación marcada como leída con éxito',
            'data': {
                'id': notification_id,
                'is_read': True
            },
            'success': True,
            'error': None
        }), 200

    except Exception as e:
        session.rollback()  # Revierte la mutación del estado si el commit de base de datos falla
        traceback.print_exc()
        return jsonify({
            'message': 'Error al actualizar el estado de lectura de la notificación',
            'data': None,
            'success': False,
            'error': str(e)
        }), 500
    finally:
        # 💡 CORRECCIÓN CRÍTICA: Se inyectó el bloque finally para evitar fugas de memoria (Memory Leaks)
        session.close()