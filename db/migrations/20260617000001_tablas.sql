-- migrate:up
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id TEXT PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100), lastname VARCHAR(100), phone VARCHAR(50), document_type VARCHAR(20), 
    document_number VARCHAR(50), avatar_url TEXT, nationality VARCHAR(50), stars_available INTEGER DEFAULT 0
);

CREATE TABLE hotels (
    id TEXT PRIMARY KEY, location_id TEXT, name VARCHAR(255) NOT NULL, description TEXT,
    stars INTEGER, phone VARCHAR(50), email VARCHAR(100), cover_image_url TEXT, is_active BOOLEAN DEFAULT 1,
    rating REAL, distance_miles REAL, available_rooms INTEGER, tags TEXT, lat REAL, lng REAL
);

CREATE TABLE room_types (
    id TEXT PRIMARY KEY, name VARCHAR(100) NOT NULL, description TEXT, base_price REAL NOT NULL, capacity INTEGER NOT NULL
);

CREATE TABLE rooms (
    id TEXT PRIMARY KEY, hotel_id TEXT NOT NULL, room_type_id TEXT NOT NULL,
    room_number VARCHAR(20) NOT NULL, floor INTEGER, is_available BOOLEAN DEFAULT 1, image_url TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
    FOREIGN KEY (room_type_id) REFERENCES room_types(id) ON DELETE CASCADE
);

CREATE TABLE additional_services (
    id TEXT PRIMARY KEY, hotel_id TEXT NOT NULL, name VARCHAR(255) NOT NULL, price REAL NOT NULL, description TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE
);

CREATE TABLE rewards (
    id TEXT PRIMARY KEY, name VARCHAR(255) NOT NULL, description TEXT, stars_cost INTEGER NOT NULL, type VARCHAR(50), is_active BOOLEAN DEFAULT 1
);

CREATE TABLE reservations (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, room_id TEXT NOT NULL, check_in TIMESTAMP NOT NULL,
    check_out TIMESTAMP NOT NULL, total_price REAL DEFAULT 0.0, status VARCHAR(50), adults INTEGER, children INTEGER,
    special_requests TEXT, created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
);

CREATE TABLE reviews (
    id TEXT PRIMARY KEY, reservation_id TEXT, user_id TEXT NOT NULL, hotel_id TEXT NOT NULL,
    rating INTEGER, comment TEXT, created_at TIMESTAMP, user_name VARCHAR(100),
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE
);

CREATE TABLE reward_redemptions (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, reward_id TEXT NOT NULL, reservation_id TEXT,
    stars_spent INTEGER NOT NULL, status VARCHAR(50), created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reward_id) REFERENCES rewards(id) ON DELETE CASCADE,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL
);

CREATE TABLE loyalty_transactions (
    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, type VARCHAR(50) NOT NULL, stars INTEGER NOT NULL,
    description TEXT, hotel_name VARCHAR(255), created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 👈 NUEVAS TABLAS REQUERIDAS POR TU APP FLASK
CREATE TABLE guests (
    id TEXT PRIMARY KEY, reservation_id TEXT, name VARCHAR(100), lastname VARCHAR(100),
    document_type VARCHAR(20), document_number VARCHAR(50), nationality VARCHAR(50),
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
);

CREATE TABLE payments (
    id TEXT PRIMARY KEY, reservation_id TEXT, amount REAL, method VARCHAR(50),
    status VARCHAR(50), paid_at TIMESTAMP, transaction_id VARCHAR(100),
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
);

CREATE TABLE reservation_services (
    id TEXT PRIMARY KEY, reservation_id TEXT, service_id TEXT, quantity INTEGER, subtotal REAL,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES additional_services(id) ON DELETE CASCADE
);

CREATE TABLE notifications (
    id TEXT PRIMARY KEY, user_id TEXT, reservation_id TEXT, title VARCHAR(255),
    body TEXT, type VARCHAR(50), is_read BOOLEAN DEFAULT 0, created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL
);

-- migrate:down
DROP TABLE IF EXISTS notifications; DROP TABLE IF EXISTS reservation_services; DROP TABLE IF EXISTS payments; DROP TABLE IF EXISTS guests;
DROP TABLE IF EXISTS loyalty_transactions; DROP TABLE IF EXISTS reward_redemptions; DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS reservations; DROP TABLE IF EXISTS rewards; DROP TABLE IF EXISTS additional_services;
DROP TABLE IF EXISTS rooms; DROP TABLE IF EXISTS room_types; DROP TABLE IF EXISTS hotels; DROP TABLE IF EXISTS users;