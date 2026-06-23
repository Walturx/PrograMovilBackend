# ==============================================================================
# ARCHIVO: hotel_ya/apis/__init__.py (o el cargador central de rutas)
# PROPÓSITO: Centralizar, estructurar e inyectar de manera limpia todos los
#            Blueprints corregidos del ecosistema "Hotel Ya" en la app de Flask.
#            Sincroniza los contratos de endpoints mapeados para Flutter.
# ==============================================================================

# BLUEPRINTS EXCLUSIVOS DEL SISTEMA HOTEL_YA
from .user import api as hotel_users                  # Gestión de Autenticación, Tokens y Perfiles (user.py)
from .hotel import api as hotel_catalog               # Exploración de Catálogo de Hoteles, Habitaciones y Detalles (hotel.py)
from .reservation import api as hotel_reserves         # Creación Transaccional de Reservas e Historial (reservation.py)
from .payments import api as hotel_payments           # Generación y Verificación de Pagos QR Interoperables (payments.py)
from .loyalty import api as hotel_loyalty             # Catálogo de Premios y Canje Atómico de Estrellas (loyalty.py)
from .services import api as hotel_services           # Cargos Extras y Consumos en la Habitación (services.py)
from .redemptions import api as hotel_redemptions     # Billetera de Cupones/Premios Canjeados (redemptions.py)
from .notifications import api as hotel_notifications # Bandeja de Entrada y Estado de Lectura de Alertas (notifications.py)

# Lista global que Flask utilizará para registrar únicamente las rutas del hotel
blueprints = [
    hotel_users,
    hotel_catalog,
    hotel_reserves,
    hotel_payments,
    hotel_loyalty,
    hotel_services,
    hotel_redemptions,
    hotel_notifications
]

def register(app):
    """
    Función encargada de iterar e inyectar de manera atómica los blueprints
    en la instancia global de la aplicación Flask.
    """
    for bp in blueprints:
        app.register_blueprint(bp)