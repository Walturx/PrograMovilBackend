-- IMPORTANTE: Ejecutar esto siempre al conectar para activar las relaciones
PRAGMA foreign_keys = ON;

-- 1. location
CREATE TABLE location (
    id_location TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL
);

-- 2. hotel
CREATE TABLE hotel (
    id_hotel TEXT PRIMARY KEY,
    location_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    stars INTEGER CHECK (stars BETWEEN 1 AND 5),
    phone TEXT,
    email TEXT,
    cover_image_url TEXT,
    is_active BOOLEAN,
    FOREIGN KEY (location_id) REFERENCES location(id_location)
);

-- 3. room_type
CREATE TABLE room_type (
    id_room_type TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    base_price FLOAT NOT NULL DEFAULT 0,
    capacity INTEGER NOT NULL
);

-- 4. room
CREATE TABLE room (
    id_room TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    room_type_id TEXT NOT NULL,
    room_number TEXT NOT NULL,
    floor INTEGER,
    is_available BOOLEAN,
    image_url TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotel(id_hotel),
    FOREIGN KEY (room_type_id) REFERENCES room_type(id_room_type)
);

-- 5. user
CREATE TABLE user (
    id_user TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    lastname TEXT,
    phone TEXT,
    document_type TEXT,
    document_number TEXT UNIQUE,
    avatar_url TEXT,
    nationality TEXT
);

-- 6. guest
CREATE TABLE guest (
    id_guest TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    name TEXT NOT NULL,
    lastname TEXT,
    document_type TEXT,
    document_number TEXT UNIQUE,
    nationality TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservation(id_reservation)
);

-- 7. reservation
CREATE TABLE reservation (
    id_reservation TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    check_in DATETIME NOT NULL,
    check_out DATETIME NOT NULL,
    total_price FLOAT NOT NULL,
    status TEXT DEFAULT 'pending',
    adults INTEGER DEFAULT 1,
    children INTEGER DEFAULT 0,
    special_requests TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id_user),
    FOREIGN KEY (room_id) REFERENCES room(id_room)
);

-- 8. payment
CREATE TABLE payment (
    id_payment TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    amount FLOAT NOT NULL,
    method TEXT,
    status TEXT DEFAULT 'pending',
    paid_at DATETIME,
    transaction_id TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservation(id_reservation)
);

-- 9. amenity
CREATE TABLE amenity (
    id_amenity TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    category TEXT
);

-- 10. hotel_amenity
CREATE TABLE hotel_amenity (
    hotel_id TEXT NOT NULL,
    amenity_id TEXT NOT NULL,
    PRIMARY KEY (hotel_id, amenity_id),
    FOREIGN KEY (hotel_id) REFERENCES hotel(id_hotel),
    FOREIGN KEY (amenity_id) REFERENCES amenity(id_amenity)
);

-- 11. room_amenity
CREATE TABLE room_amenity (
    room_id TEXT NOT NULL,
    amenity_id TEXT NOT NULL,
    PRIMARY KEY (room_id, amenity_id),
    FOREIGN KEY (room_id) REFERENCES room(id_room),
    FOREIGN KEY (amenity_id) REFERENCES amenity(id_amenity)
);

-- 12. service
CREATE TABLE service (
    id_service TEXT PRIMARY KEY,
    hotel_id TEXT NOT NULL,
    name TEXT NOT NULL,
    price FLOAT NOT NULL,
    description TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotel(id_hotel)
);

-- 13. reservation_service
CREATE TABLE reservation_service (
    id_reservation_service TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    subtotal FLOAT NOT NULL,
    FOREIGN KEY (reservation_id) REFERENCES reservation(id_reservation),
    FOREIGN KEY (service_id) REFERENCES service(id_service)
);

-- 14. loyalty_transaction
CREATE TABLE loyalty_transaction (
    id_loyalty_transaction TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    reservation_id TEXT,
    reward_redemption_id TEXT,
    type TEXT NOT NULL,
    stars INTEGER NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id_user),
    FOREIGN KEY (reservation_id) REFERENCES reservation(id_reservation),
    FOREIGN KEY (reward_redemption_id) REFERENCES reward_redemption(id_reward_redemption)
);

-- 15. reward
CREATE TABLE reward (
    id_reward TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    stars_cost INTEGER NOT NULL,
    type TEXT,
    is_active BOOLEAN
);

-- 16. reward_redemption
CREATE TABLE reward_redemption (
    id_reward_redemption TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    reward_id TEXT NOT NULL,
    reservation_id TEXT,
    stars_spent INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id_user),
    FOREIGN KEY (reward_id) REFERENCES reward(id_reward),
    FOREIGN KEY (reservation_id) REFERENCES reservation(id_reservation)
);

-- 17. review
CREATE TABLE review (
    id_review TEXT PRIMARY KEY,
    reservation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    hotel_id TEXT NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservation(id_reservation),
    FOREIGN KEY (user_id) REFERENCES user(id_user),
    FOREIGN KEY (hotel_id) REFERENCES hotel(id_hotel)
);

-- 18. notification
CREATE TABLE notification (
    id_notification TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    reservation_id TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    type TEXT,
    is_read BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id_user),
    FOREIGN KEY (reservation_id) REFERENCES reservation(id_reservation)
);