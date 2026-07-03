-- migrate:up
PRAGMA foreign_keys = ON;
PRAGMA foreign_keys = ON;

-- 1. LOCATIONS
CREATE TABLE locations (
    id_location TEXT PRIMARY KEY,
    country TEXT,
    city TEXT,
    state TEXT
);

-- 2. USERS
CREATE TABLE users (
    id_user TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    lastname TEXT,
    phone TEXT,
    birthdate TEXT,
    age INTEGER,
    document_type TEXT,
    document_number TEXT,
    avatar_url TEXT,
    nationality TEXT,
    reset_password_token INTEGER,
    status BOOLEAN DEFAULT 1,
    stars_available INTEGER DEFAULT 0,
    user_name VARCHAR(20),
    password VARCHAR(250),
    member_id INTEGER
);

-- 3. HOTELS
CREATE TABLE hotels (
    id_hotel TEXT PRIMARY KEY,
    location_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    stars INTEGER,
    phone TEXT,
    email TEXT,
    cover_image_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (location_id) REFERENCES locations(id_location) ON DELETE SET NULL
);

-- 4. ROOM_TYPES
CREATE TABLE room_types (
    id_room_type TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    base_price FLOAT NOT NULL,
    capacity INTEGER NOT NULL
);

-- 5. ROOMS
CREATE TABLE rooms (
    id_room TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    room_type_id TEXT NOT NULL,
    room_number TEXT NOT NULL,
    floor INTEGER,
    is_available BOOLEAN DEFAULT 1,
    image_url TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id_hotel) ON DELETE CASCADE,
    FOREIGN KEY (room_type_id) REFERENCES room_types(id_room_type) ON DELETE CASCADE
);

-- 6. AMENITIES
CREATE TABLE amenities (
    id_amenity TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    category TEXT
);

-- 7. HOTEL_AMENITIES (Tabla Pivot)
CREATE TABLE hotel_amenities (
    hotel_id TEXT NOT NULL,
    amenity_id TEXT NOT NULL,
    PRIMARY KEY (hotel_id, amenity_id),
    FOREIGN KEY (hotel_id) REFERENCES hotels(id_hotel) ON DELETE CASCADE,
    FOREIGN KEY (amenity_id) REFERENCES amenities(id_amenity) ON DELETE CASCADE
);

-- 8. ROOM_AMENITIES (Tabla Pivot)
CREATE TABLE room_amenities (
    room_id TEXT NOT NULL,
    amenity_id TEXT NOT NULL,
    PRIMARY KEY (room_id, amenity_id),
    FOREIGN KEY (room_id) REFERENCES rooms(id_room) ON DELETE CASCADE,
    FOREIGN KEY (amenity_id) REFERENCES amenities(id_amenity) ON DELETE CASCADE
);

-- 9. SERVICES
CREATE TABLE services (
    id_service TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    name TEXT NOT NULL,
    price FLOAT NOT NULL,
    description TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id_hotel) ON DELETE CASCADE
);

-- 10. RESERVATIONS
CREATE TABLE reservations (
    id_reservation TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    check_in DATETIME NOT NULL,
    check_out DATETIME NOT NULL,
    total_price FLOAT DEFAULT 0.0,
    status TEXT,
    adults INTEGER,
    children INTEGER,
    special_requests TEXT,
    created_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id_room) ON DELETE CASCADE
);

-- 11. GUESTS
CREATE TABLE guests (
    id_guest TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    name TEXT,
    lastname TEXT,
    document_type TEXT,
    document_number TEXT,
    nationality TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id_reservation) ON DELETE CASCADE
);

-- 12. PAYMENTS
CREATE TABLE payments (
    id_payment TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    amount FLOAT NOT NULL,
    method TEXT,
    status TEXT,
    paid_at DATETIME,
    transaction_id TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id_reservation) ON DELETE CASCADE
);

-- 13. RESERVATION_SERVICES (Tabla Pivot)
CREATE TABLE reservation_services (
    id_reservation_service TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    subtotal FLOAT DEFAULT 0.0,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id_reservation) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id_service) ON DELETE CASCADE
);

-- 14. REWARDS
CREATE TABLE rewards (
    id_reward TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    stars_cost INTEGER NOT NULL,
    type TEXT,
    is_active BOOLEAN DEFAULT 1
);

-- 15. REWARD_REDEMPTIONS
CREATE TABLE reward_redemptions (
    id_reward_redemption TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    reward_id TEXT NOT NULL,
    reservation_id TEXT,
    stars_spent INTEGER NOT NULL,
    status TEXT,
    created_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (reward_id) REFERENCES rewards(id_reward) ON DELETE CASCADE,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id_reservation) ON DELETE SET NULL
);

-- 16. LOYALTY_TRANSACTIONS
CREATE TABLE loyalty_transactions (
    id_loyalty_transaction TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    reservation_id TEXT,
    reward_redemption_id TEXT,
    type TEXT NOT NULL,
    stars INTEGER NOT NULL,
    description TEXT,
    created_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id_reservation) ON DELETE SET NULL,
    FOREIGN KEY (reward_redemption_id) REFERENCES reward_redemptions(id_reward_redemption) ON DELETE SET NULL
);

-- 17. REVIEWS
CREATE TABLE reviews (
    id_review TEXT PRIMARY KEY,
    reservation_id TEXT,
    user_id TEXT NOT NULL,
    hotel_id TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at DATETIME,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id_reservation) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id_hotel) ON DELETE CASCADE
);

-- migrate:down
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS loyalty_transactions;
DROP TABLE IF EXISTS reward_redemptions;
DROP TABLE IF EXISTS rewards;
DROP TABLE IF EXISTS reservation_services;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS guests;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS room_amenities;
DROP TABLE IF EXISTS hotel_amenities;
DROP TABLE IF EXISTS amenities;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS room_types;
DROP TABLE IF EXISTS hotels;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS locations;