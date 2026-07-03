from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime, Table
from sqlalchemy.orm import declarative_base, relationship
from main.database import ToString
import datetime

Base = declarative_base()

# ==========================================
# TABLAS INTERMEDIAS (Muchos a Muchos)
# ==========================================

hotel_amenities = Table('hotel_amenities', Base.metadata,
    Column('hotel_id', String, ForeignKey('hotels.id_hotel', ondelete="CASCADE"), primary_key=True),
    Column('amenity_id', String, ForeignKey('amenities.id_amenity', ondelete="CASCADE"), primary_key=True)
)

room_amenities = Table('room_amenities', Base.metadata,
    Column('room_id', String, ForeignKey('rooms.id_room', ondelete="CASCADE"), primary_key=True),
    Column('amenity_id', String, ForeignKey('amenities.id_amenity', ondelete="CASCADE"), primary_key=True)
)

# ==========================================
# MODELOS PRINCIPALES
# ==========================================

class Location(Base, ToString):
    __tablename__ = 'locations'
    id_location = Column(String, primary_key=True)
    country = Column(String)
    city = Column(String)
    state = Column(String)

    hotels = relationship('Hotel', back_populates='location')


class Hotel(Base, ToString):
    __tablename__ = 'hotels'
    id_hotel = Column(String, primary_key=True)
    location_id = Column(String, ForeignKey('locations.id_location', ondelete="SET NULL"))
    name = Column(String, nullable=False)
    description = Column(String)
    stars = Column(Integer)
    phone = Column(String)
    email = Column(String)
    cover_image_url = Column(String)
    is_active = Column(Boolean, default=True)

    location = relationship('Location', back_populates='hotels')
    rooms = relationship('Room', back_populates='hotel')
    services = relationship('Service', back_populates='hotel')
    reviews = relationship('Review', back_populates='hotel')
    amenities = relationship('Amenity', secondary=hotel_amenities, back_populates='hotels')


class RoomType(Base, ToString):
    __tablename__ = 'room_types'
    id_room_type = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    base_price = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)

    rooms = relationship('Room', back_populates='room_type')


class Room(Base, ToString):
    __tablename__ = 'rooms'
    id_room = Column(String, primary_key=True)
    hotel_id = Column(String, ForeignKey('hotels.id_hotel', ondelete="CASCADE"), nullable=False)
    room_type_id = Column(String, ForeignKey('room_types.id_room_type', ondelete="CASCADE"), nullable=False)
    room_number = Column(String, nullable=False)
    floor = Column(Integer)
    is_available = Column(Boolean, default=True)
    image_url = Column(String)

    hotel = relationship('Hotel', back_populates='rooms')
    room_type = relationship('RoomType', back_populates='rooms')
    reservations = relationship('Reservation', back_populates='room')
    amenities = relationship('Amenity', secondary=room_amenities, back_populates='rooms')


class Amenity(Base, ToString):
    __tablename__ = 'amenities'
    id_amenity = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    icon = Column(String)
    category = Column(String)

    hotels = relationship('Hotel', secondary=hotel_amenities, back_populates='amenities')
    rooms = relationship('Room', secondary=room_amenities, back_populates='amenities')


class User(Base, ToString):
    __tablename__ = 'users'
    id_user = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    lastname = Column(String)
    phone = Column(String)
    birthdate = Column(String)  # Sincronizado como TEXT en SQLite
    age = Column(Integer)
    document_type = Column(String)
    document_number = Column(String)
    avatar_url = Column(String)
    nationality = Column(String)
    reset_password_token = Column(Integer)
    status = Column(Boolean, default=True)
    stars_available = Column(Integer, default=0)

    reservations = relationship('Reservation', back_populates='user')
    loyalty_transactions = relationship('LoyaltyTransaction', back_populates='user')
    reward_redemptions = relationship('RewardRedemption', back_populates='user')
    reviews = relationship('Review', back_populates='user')


class Reservation(Base, ToString):
    __tablename__ = 'reservations'
    id_reservation = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id_user', ondelete="CASCADE"), nullable=False)
    room_id = Column(String, ForeignKey('rooms.id_room', ondelete="CASCADE"), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    total_price = Column(Float, default=0.0)
    status = Column(String)
    adults = Column(Integer)
    children = Column(Integer)
    special_requests = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='reservations')
    room = relationship('Room', back_populates='reservations')
    guests = relationship('Guest', back_populates='reservation')
    payments = relationship('Payment', back_populates='reservation')
    reservation_services = relationship('ReservationService', back_populates='reservation')
    reviews = relationship('Review', back_populates='reservation')


class Guest(Base, ToString):
    __tablename__ = 'guests'
    id_guest = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id_reservation', ondelete="CASCADE"), nullable=False)
    name = Column(String)
    lastname = Column(String)
    document_type = Column(String)
    document_number = Column(String)
    nationality = Column(String)

    reservation = relationship('Reservation', back_populates='guests')


class Payment(Base, ToString):
    __tablename__ = 'payments'
    id_payment = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id_reservation', ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String)
    status = Column(String)
    paid_at = Column(DateTime)
    transaction_id = Column(String)

    reservation = relationship('Reservation', back_populates='payments')


class Service(Base, ToString):
    __tablename__ = 'services'
    id_service = Column(String, primary_key=True)
    hotel_id = Column(String, ForeignKey('hotels.id_hotel', ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String)

    hotel = relationship('Hotel', back_populates='services')


class ReservationService(Base, ToString):
    __tablename__ = 'reservation_services'
    id_reservation_service = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id_reservation', ondelete="CASCADE"), nullable=False)
    service_id = Column(String, ForeignKey('services.id_service', ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1)
    subtotal = Column(Float, default=0.0)

    reservation = relationship('Reservation', back_populates='reservation_services')
    service = relationship('Service')


class Reward(Base, ToString):
    __tablename__ = 'rewards'
    id_reward = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    stars_cost = Column(Integer, nullable=False)
    type = Column(String)
    is_active = Column(Boolean, default=True)


class RewardRedemption(Base, ToString):
    __tablename__ = 'reward_redemptions'
    id_reward_redemption = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id_user', ondelete="CASCADE"), nullable=False)
    reward_id = Column(String, ForeignKey('rewards.id_reward', ondelete="CASCADE"), nullable=False)
    reservation_id = Column(String, ForeignKey('reservations.id_reservation', ondelete="SET NULL"), nullable=True)
    stars_spent = Column(Integer, nullable=False)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='reward_redemptions')
    reward = relationship('Reward')


class LoyaltyTransaction(Base, ToString):
    __tablename__ = 'loyalty_transactions'
    id_loyalty_transaction = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id_user', ondelete="CASCADE"), nullable=False)
    reservation_id = Column(String, ForeignKey('reservations.id_reservation', ondelete="SET NULL"), nullable=True)
    reward_redemption_id = Column(String, ForeignKey('reward_redemptions.id_reward_redemption', ondelete="SET NULL"), nullable=True)
    type = Column(String, nullable=False) 
    stars = Column(Integer, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='loyalty_transactions')


class Review(Base, ToString):
    __tablename__ = 'reviews'
    id_review = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.id_reservation', ondelete="SET NULL"), nullable=True)
    user_id = Column(String, ForeignKey('users.id_user', ondelete="CASCADE"), nullable=False)
    hotel_id = Column(String, ForeignKey('hotels.id_hotel', ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reservation = relationship('Reservation', back_populates='reviews')
    user = relationship('User', back_populates='reviews')
    hotel = relationship('Hotel', back_populates='reviews')


def model_to_dict(self):
    dict_data = {}
    for column in self.__table__.columns:
        value = getattr(self, column.name)
        if isinstance(value, (datetime.datetime, datetime.date)):
            value = value.isoformat()
        dict_data[column.name] = value
    return dict_data

Base.to_dict = model_to_dict