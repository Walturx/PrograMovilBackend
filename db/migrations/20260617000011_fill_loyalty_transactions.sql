-- migrate:up
INSERT INTO loyalty_transactions (id, user_id, type, stars, description, hotel_name, created_at) VALUES 
('lt1', 'u1', 'earned', 5, 'Reserva completada', 'Hotel Paradise', '2024-03-12'),
('lt2', 'u1', 'spent', 5, 'Helado Premium', NULL, '2024-03-13'),
('lt3', 'u1', 'spent', 5, 'Helado Premium', NULL, '2024-03-15'),
('lt4', 'u1', 'spent', 30, '1 Noche Gratis', NULL, '2024-03-20');

-- migrate:down
DELETE FROM loyalty_transactions;