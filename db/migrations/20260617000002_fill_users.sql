-- migrate:up
INSERT INTO users (id, email, password_hash, name, lastname, phone, document_type, document_number, avatar_url, nationality, stars_available) VALUES 
('u1', 'juan@email.com', '123456', 'Juan', 'Pérez', '+51 999999999', 'DNI', '12345678', 'https://i.pravatar.cc/300', 'Peruano', 1200);
-- migrate:down
DELETE FROM users;