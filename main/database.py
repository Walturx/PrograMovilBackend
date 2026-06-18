import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class ToString:
    def to_dict(self):
        # Convierte los atributos del modelo en un diccionario manejando fechas de forma segura
        dict_data = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):  # Excluye atributos internos de SQLAlchemy
                # Si es una fecha o tiempo, la convertimos a formato texto ISO para que JSON no falle
                if isinstance(value, (datetime.datetime, datetime.date)):
                    value = value.isoformat()
                dict_data[key] = value
        return dict_data
  
    def __repr__(self):
        return f"<{self.__class__.__name__}({', '.join(f'{key}={value}' for key, value in self.__dict__.items() if not key.startswith('_'))})>"

engine = create_engine("sqlite:///db/app.db", echo=True)
Session = sessionmaker(bind=engine)