-- migrate:up
INSERT INTO users (id_user, email, password_hash, name, lastname, phone, birthdate, age, document_type, document_number, avatar_url, nationality, reset_password_token, status) VALUES 
('u1', 'juan@email.com', '123456', 'Juan', 'Pérez', '+51 999999999', NULL, NULL, 'DNI', '12345678', 'https://i.pravatar.cc/300', 'Peruano', NULL, 1);

-- migrate:down
DELETE FROM users WHERE id_user = 'u1';