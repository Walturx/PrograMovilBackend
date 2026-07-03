from main.views import view as main_views
from main.apis import api as main_apis

# Importamos uno por uno los submódulos reales de hotel_ya/apis/
from hotel_ya.apis.home import api as hotel_home
from hotel_ya.apis.user import api as hotel_users
from hotel_ya.apis.hotel import api as hotel_catalog
from hotel_ya.apis.reservation import api as hotel_reserves
from hotel_ya.apis.payments import api as hotel_payments
from hotel_ya.apis.loyalty import api as hotel_loyalty
from hotel_ya.apis.services import api as hotel_services
from hotel_ya.apis.redemptions import api as hotel_redemptions

def register(app):
  # Empaquetamos en la lista manteniendo exactamente tu estilo
  modules_blueprints = [
    [
      hotel_home,
      hotel_users,
      hotel_catalog,
      hotel_reserves,
      hotel_payments,
      hotel_loyalty,
      hotel_services,
      hotel_redemptions
    ]
  ]
  
  # load main blueprint to app
  app.register_blueprint(main_views)
  app.register_blueprint(main_apis)
  
  # load sub blueprints to app utilizando el doble for que querías
  for blueprints in modules_blueprints:
    for blueprint in blueprints:
      app.register_blueprint(blueprint)