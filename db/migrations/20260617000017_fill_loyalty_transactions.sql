-- migrate:up
INSERT INTO loyalty_transactions (id_loyalty_transaction, user_id, reservation_id, reward_redemption_id, type, stars, description, created_at) VALUES 
('lt1', 'u1', 'res1', NULL, 'earned', 5, 'Reserva completada', '2024-03-12'),
('lt2', 'u1', NULL, 'rr1', 'spent', 5, 'Helado Premium', '2024-03-13'),
('lt3', 'u1', NULL, 'rr1', 'spent', 5, 'Helado Premium', '2024-03-15'),
('lt4', 'u1', 'res1', 'rr2', 'spent', 30, '1 Noche Gratis', '2024-03-20');

-- migrate:down
DELETE FROM loyalty_transactions WHERE id_loyalty_transaction IN ('lt1', 'lt2', 'lt3', 'lt4');