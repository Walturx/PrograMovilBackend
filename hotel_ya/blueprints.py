# =========================================================
# BLUEPRINTS EXCLUSIVOS DEL SISTEMA HOTEL_YA
# =========================================================
from .apis.auth import api as hotel_auth                # Módulo de Autenticación (Login, Registro, Tokens)
from .apis.user import api as hotel_users               # Módulo de Gestión de Perfiles y Datos de Usuario
from .apis.hotel import api as hotel_catalog             # Módulo de Exploración de Hoteles y Habitaciones
from .apis.reservation import api as hotel_reserves       # Módulo de Reservas, Acompañantes y Pagos QR
from .apis.rewards import api as hotel_rewards             # Módulo de Catálogo de Premios y Canje Directo
from .apis.loyalty import api as hotel_loyalty             # Módulo de Historial de Transacciones de Estrellas
from .apis.services import api as hotel_services           # Módulo de Room Service y Solicitudes Extras
from .apis.redemptions import api as hotel_redemptions     # Módulo de Historial de Cupones QR Canjeados

# Lista global que Flask utilizará para registrar únicamente las rutas del hotel
blueprints = [
    hotel_auth,
    hotel_users,
    hotel_catalog,
    hotel_reserves,
    hotel_rewards,
    hotel_loyalty,
    hotel_services,
    hotel_redemptions
]

def register(app):
    """
    Función encargada de iterar e inyectar los blueprints en la aplicación Flask.
    """
    for bp in blueprints:
        app.register_blueprint(bp)