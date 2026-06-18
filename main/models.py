from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime, Table
from sqlalchemy.orm import declarative_base, relationship
from main.database import ToString
import datetime

Base = declarative_base()

# ==========================================
# TABLAS INTERMEDIAS (Muchos a Muchos)
# ==========================================

hotel_amenities = Table('hotel_amenities', Base.metadata,
    Column('hotel_id', String, ForeignKey('hotels.id'), primary_key=True),
    Column('amenity_id', String, ForeignKey('amenities.id'), primary_key=True)
)

room_amenities = Table('room_amenities', Base.metadata,
    Column('room_id', String, ForeignKey('rooms.id'), primary_key=True),
    Column('amenity_id', String, ForeignKey('amenities.id'), primary_key=True)
)

# ==========================================
# MODELOS PRINCIPALES
# ==========================================

class Hotel(Base, ToString):
    __tablename__ = 'hotels'
    id = Column(String, primary_key=True)
    location_id = Column(String)  # Simple String sin FK externa
    name = Column(String, nullable=False)
    description = Column(String)
    stars = Column(Integer)
    phone = Column(String)
    email = Column(String)
    cover_image_url = Column(String)
    is_active = Column(Boolean, default=True)
    rating = Column(Float)
    distance_miles = Column(Float)
    available_rooms = Column(Integer)
    tags = Column(String)  
    lat = Column(Float)
    lng = Column(Float)

    rooms = relationship('Room', back_populates='hotel', cascade="all, delete-orphan")
    services = relationship('Service', back_populates='hotel', cascade="all, delete-orphan")
    reviews = relationship('Review', back_populates='hotel', cascade="all, delete-orphan")
    amenities = relationship('Amenity', secondary=hotel_amenities, back_populates='hotels')

class RoomType(Base, ToString):
    __tablename__ = 'room_types'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    base_price = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)

    rooms = relationship('Room', back_populates='room_type', cascade="all, delete-orphan")


class Room(Base, ToString):
    __tablename__ = 'rooms'
    id = Column(String, primary_key=True)
    hotel_id = Column(String, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False)
    room_type_id = Column(String, ForeignKey('room_types.id', ondelete='CASCADE'), nullable=False)
    room_number = Column(String, nullable=False)
    floor = Column(Integer)
    is_available = Column(Boolean, default=True)
    image_url = Column(String)

    hotel = relationship('Hotel', back_populates='rooms')
    room_type = relationship('RoomType', back_populates='rooms')
    reservations = relationship('Reservation', back_populates='room', cascade="all, delete-orphan")
    amenities = relationship('Amenity', secondary=room_amenities, back_populates='rooms')


class Amenity(Base, ToString):
    __tablename__ = 'amenities'
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String)
    category = Column(String)

    hotels = relationship('Hotel', secondary=hotel_amenities, back_populates='amenities')
    rooms = relationship('Room', secondary=room_amenities, back_populates='amenities')

# ==========================================
# SERVICIOS ADICIONALES
# ==========================================

class Service(Base, ToString):
    __tablename__ = 'additional_services'  
    id = Column(String, primary_key=True)
    hotel_id = Column(String, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String)

    hotel = relationship('Hotel', back_populates='services')


class ReservationService(Base, ToString):
    __tablename__ = 'reservation_services'  # 👈 Restaurado para tus APIs
    id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id', ondelete='CASCADE'))
    service_id = Column(String, ForeignKey('additional_services.id', ondelete='CASCADE'))
    quantity = Column(Integer)
    subtotal = Column(Float)

    reservation = relationship('Reservation', back_populates='reservation_services')
    service = relationship('Service')

# ==========================================
# USUARIOS Y RESERVAS
# ==========================================

class User(Base, ToString):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    lastname = Column(String)
    phone = Column(String)
    document_type = Column(String)
    document_number = Column(String)
    avatar_url = Column(String)
    nationality = Column(String)
    stars_available = Column(Integer, default=0)

    reservations = relationship('Reservation', back_populates='user', cascade="all, delete-orphan")
    loyalty_transactions = relationship('LoyaltyTransaction', back_populates='user', cascade="all, delete-orphan")
    reward_redemptions = relationship('RewardRedemption', back_populates='user', cascade="all, delete-orphan")
    reviews = relationship('Review', back_populates='user', cascade="all, delete-orphan")
    notifications = relationship('Notification', back_populates='user', cascade="all, delete-orphan")


class Reservation(Base, ToString):
    __tablename__ = 'reservations'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    room_id = Column(String, ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String)  
    adults = Column(Integer)
    children = Column(Integer)
    special_requests = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='reservations')
    room = relationship('Room', back_populates='reservations')
    guests = relationship('Guest', back_populates='reservation', cascade="all, delete-orphan") # 👈 Restaurado
    payments = relationship('Payment', back_populates='reservation', cascade="all, delete-orphan") # 👈 Restaurado
    reservation_services = relationship('ReservationService', back_populates='reservation', cascade="all, delete-orphan") # 👈 Restaurado
    reviews = relationship('Review', back_populates='reservation')
    reward_redemptions = relationship('RewardRedemption', back_populates='reservation')


class Guest(Base, ToString):
    __tablename__ = 'guests'  # 👈 ¡Mapeado e importable con éxito!
    id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id', ondelete='CASCADE'))
    name = Column(String)
    lastname = Column(String)
    document_type = Column(String)
    document_number = Column(String)
    nationality = Column(String)

    reservation = relationship('Reservation', back_populates='guests')


class Payment(Base, ToString):
    __tablename__ = 'payments'  # 👈 ¡Mapeado e importable con éxito!
    id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id', ondelete='CASCADE'))
    amount = Column(Float)
    method = Column(String)
    status = Column(String)
    paid_at = Column(DateTime)
    transaction_id = Column(String)

    reservation = relationship('Reservation', back_populates='payments')


class Review(Base, ToString):
    __tablename__ = 'reviews'
    id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id', ondelete='SET NULL'), nullable=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    hotel_id = Column(String, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer)
    comment = Column(String)
    user_name = Column(String)  
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reservation = relationship('Reservation', back_populates='reviews')
    user = relationship('User', back_populates='reviews')
    hotel = relationship('Hotel', back_populates='reviews')

# ==========================================
# FIDELIDAD, RECOMPENSAS Y NOTIFICACIONES
# ==========================================

class Reward(Base, ToString):
    __tablename__ = 'rewards'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    stars_cost = Column(Integer, nullable=False)
    type = Column(String)
    is_active = Column(Boolean, default=True)


class RewardRedemption(Base, ToString):
    __tablename__ = 'reward_redemptions'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reward_id = Column(String, ForeignKey('rewards.id', ondelete='CASCADE'), nullable=False)
    reservation_id = Column(String, ForeignKey('reservations.id', ondelete='SET NULL'), nullable=True)
    stars_spent = Column(Integer, nullable=False)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='reward_redemptions')
    reward = relationship('Reward')
    reservation = relationship('Reservation', back_populates='reward_redemptions')


class LoyaltyTransaction(Base, ToString):
    __tablename__ = 'loyalty_transactions'
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = Column(String, nullable=False)  
    stars = Column(Integer, nullable=False)
    description = Column(String)
    hotel_name = Column(String)  
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='loyalty_transactions')


class Notification(Base, ToString):
    __tablename__ = 'notifications'  # 👈 Restaurado para tus alertas
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'))
    reservation_id = Column(String, ForeignKey('reservations.id', ondelete='SET NULL'), nullable=True)
    title = Column(String)
    body = Column(String)
    type = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='notifications')


# ==========================================
# EXTENSIÓN PARA SERIALIZACIÓN A DICCIONARIO
# ==========================================
def model_to_dict(self):
    dict_data = {}
    for column in self.__table__.columns:
        value = getattr(self, column.name)
        if isinstance(value, (datetime.datetime, datetime.date)):
            value = value.isoformat()
        dict_data[column.name] = value
    return dict_data

Base.to_dict = model_to_dict