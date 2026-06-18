from main.views import view as main_views
from main.apis import api as main_apis
# Adaptado: Importamos la lista 'blueprints' desde la carpeta de tu sistema HOTEL_YA
from hotel_ya.blueprints import blueprints as hotel_blueprints

def register(app):
    # append sub blueprints
    # Adaptado: Colocamos 'hotel_blueprints' dentro de tu lista original
    modules_blueprints = [
        hotel_blueprints,
    ]
    
    # load main blueprint to app
    app.register_blueprint(main_views)
    app.register_blueprint(main_apis)
    
    # load sub blueprints to app (Tu ciclo original intacto)
    for blueprints in modules_blueprints:
        for blueprint in blueprints:
            app.register_blueprint(blueprint)