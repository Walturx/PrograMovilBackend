# !/usr/bin/env python
# -*- coding: utf-8 -*-
from main.application import APP
from main.blueprints import register
from main.middlewares import not_found

# --- AGREGAMOS ESTAS DOS IMPORTACIONES PARA LA BASE DE DATOS ---
from main.database import engine
from main.models import Base

if __name__ == '__main__':
  register(APP)
  APP.register_error_handler(404, not_found)
  
  # --- FORZAMOS LA CREACIÓN DE TODAS LAS TABLAS DEL HOTEL ---
  with APP.app_context():
    Base.metadata.create_all(bind=engine)
    print("¡Base de datos y tablas del hotel sincronizadas con éxito!")

  # run app
  APP.run(
    debug=True,
    host='0.0.0.0',
    port=5000
  )