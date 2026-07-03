from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, TEXT
from sqlalchemy.orm import declarative_base, relationship
from main.database import ToString
from datetime import datetime

Base = declarative_base()

# ==========================================
# 1. LOCATIONS & HOTELS
# ==========================================

class Location(Base, ToString):
    __tablename__ = 'locations'
    id_location = Column(TEXT, primary_key=True)
    country = Column(TEXT)
    city = Column(TEXT)
    state = Column(TEXT)

class Hotel(Base, ToString):
    __tablename__ = 'hotels'
    id_hotel = Column(TEXT, primary_key=True)
    location_id = Column(TEXT, ForeignKey('locations.id_location'))
    name = Column(TEXT, nullable=False)
    description = Column(TEXT)
    stars = Column(Integer)
    phone = Column(TEXT)
    email = Column(TEXT)
    cover_image_url = Column(TEXT)
    is_active = Column(Boolean, default=True)

# ==========================================
# 2. USERS, MEMBERS & AUTENTICACIÓN
# ==========================================

class Member(Base, ToString):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(40))
    codigo = Column(String(5))
    dni = Column(String(8))
    email = Column(String(40))
    phone = Column(String(40))
    users = relationship("User", back_populates="member")

class User(Base, ToString):
    __tablename__ = 'users'
    id_user = Column(TEXT, primary_key=True)
    email = Column(TEXT, unique=True, nullable=False)
    password_hash = Column(TEXT, nullable=False)
    user_name = Column(String(20), nullable=True)
    password = Column(String(250), nullable=True)
    name = Column(TEXT)
    lastname = Column(TEXT)
    phone = Column(TEXT)
    birthdate = Column(TEXT)
    age = Column(Integer)
    document_type = Column(TEXT)
    document_number = Column(TEXT)
    avatar_url = Column(TEXT)
    nationality = Column(TEXT)
    stars_available = Column(Integer, default=0) # <-- AGREGA ESTA LÍNEA AQUÍ
    reset_password_token = Column(Integer)
    status = Column(Boolean, default=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=True)
    member = relationship("Member", back_populates="users")

# ==========================================
# 3. ROOM TYPES & ROOMS
# ==========================================

class RoomType(Base, ToString):
    __tablename__ = 'room_types'
    id_room_type = Column(TEXT, primary_key=True)
    name = Column(TEXT, nullable=False)
    description = Column(TEXT)
    base_price = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)

class Room(Base, ToString):
    __tablename__ = 'rooms'
    id_room = Column(TEXT, primary_key=True)
    hotel_id = Column(TEXT, ForeignKey('hotels.id_hotel'), nullable=False)
    room_type_id = Column(TEXT, ForeignKey('room_types.id_room_type'), nullable=False)
    room_number = Column(TEXT, nullable=False)
    floor = Column(Integer)
    is_available = Column(Boolean, default=True)
    image_url = Column(TEXT)

# ==========================================
# 4. AMENITIES & PIVOT TABLES
# ==========================================

class Amenity(Base, ToString):
    __tablename__ = 'amenities'
    id_amenity = Column(TEXT, primary_key=True)
    name = Column(TEXT, nullable=False)
    icon = Column(TEXT)
    category = Column(TEXT)

class HotelAmenity(Base, ToString):
    __tablename__ = 'hotel_amenities'
    hotel_id = Column(TEXT, ForeignKey('hotels.id_hotel'), primary_key=True)
    amenity_id = Column(TEXT, ForeignKey('amenities.id_amenity'), primary_key=True)

class RoomAmenity(Base, ToString):
    __tablename__ = 'room_amenities'
    room_id = Column(TEXT, ForeignKey('rooms.id_room'), primary_key=True)
    amenity_id = Column(TEXT, ForeignKey('amenities.id_amenity'), primary_key=True)

# ==========================================
# 5. SERVICES & RESERVATIONS
# ==========================================

class Service(Base, ToString):
    __tablename__ = 'services'
    id_service = Column(TEXT, primary_key=True)
    hotel_id = Column(TEXT, ForeignKey('hotels.id_hotel'), nullable=False)
    name = Column(TEXT, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(TEXT)

class Reservation(Base, ToString):
    __tablename__ = 'reservations'
    id_reservation = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey('users.id_user'), nullable=False)
    room_id = Column(TEXT, ForeignKey('rooms.id_room'), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    total_price = Column(Float, default=0.0)
    status = Column(TEXT)
    adults = Column(Integer)
    children = Column(Integer)
    special_requests = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)

class Guest(Base, ToString):
    __tablename__ = 'guests'
    id_guest = Column(TEXT, primary_key=True)
    reservation_id = Column(TEXT, ForeignKey('reservations.id_reservation'), nullable=False)
    name = Column(TEXT)
    lastname = Column(TEXT)
    document_type = Column(TEXT)
    document_number = Column(TEXT)
    nationality = Column(TEXT)

class ReservationService(Base, ToString):
    __tablename__ = 'reservation_services'
    id_reservation_service = Column(TEXT, primary_key=True)
    reservation_id = Column(TEXT, ForeignKey('reservations.id_reservation'), nullable=False)
    service_id = Column(TEXT, ForeignKey('services.id_service'), nullable=False)
    quantity = Column(Integer, default=1)
    subtotal = Column(Float, default=0.0)

# ==========================================
# 6. PAYMENTS & REWARDS (LOYALTY)
# ==========================================

class Payment(Base, ToString):
    __tablename__ = 'payments'
    id_payment = Column(TEXT, primary_key=True)
    reservation_id = Column(TEXT, ForeignKey('reservations.id_reservation'), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(TEXT)
    status = Column(TEXT)
    paid_at = Column(DateTime)
    transaction_id = Column(TEXT)

class Reward(Base, ToString):
    __tablename__ = 'rewards'
    id_reward = Column(TEXT, primary_key=True)
    name = Column(TEXT, nullable=False)
    description = Column(TEXT)
    stars_cost = Column(Integer, nullable=False)
    type = Column(TEXT)
    is_active = Column(Boolean, default=True)

class RewardRedemption(Base, ToString):
    __tablename__ = 'reward_redemptions'
    id_reward_redemption = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey('users.id_user'), nullable=False)
    reward_id = Column(TEXT, ForeignKey('rewards.id_reward'), nullable=False)
    reservation_id = Column(TEXT, ForeignKey('reservations.id_reservation'), nullable=True)
    stars_spent = Column(Integer, nullable=False)
    status = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)

    reward = relationship("Reward")

class LoyaltyTransaction(Base, ToString):
    __tablename__ = 'loyalty_transactions'
    id_loyalty_transaction = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey('users.id_user'), nullable=False)
    reservation_id = Column(TEXT, ForeignKey('reservations.id_reservation'), nullable=True)
    reward_redemption_id = Column(TEXT, ForeignKey('reward_redemptions.id_reward_redemption'), nullable=True)
    type = Column(TEXT, nullable=False)
    stars = Column(Integer, nullable=False)
    description = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================================
# 7. REVIEWS
# ==========================================

class Review(Base, ToString):
    __tablename__ = 'reviews'
    id_review = Column(TEXT, primary_key=True)
    reservation_id = Column(TEXT, ForeignKey('reservations.id_reservation'), nullable=True)
    user_id = Column(TEXT, ForeignKey('users.id_user'), nullable=False)
    hotel_id = Column(TEXT, ForeignKey('hotels.id_hotel'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)