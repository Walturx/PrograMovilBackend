-- migrate:up
INSERT INTO notifications (id_notification, user_id, reservation_id, title, body, type, is_read, created_at) VALUES 
('ntf-1', 'u1', 'res1', '¡Reserva Confirmada!', 'Tu estadía en Palacio del Inka está lista.', 'Transaccional', 1, '2026-06-22 12:01:00');

-- migrate:down
DELETE FROM notifications WHERE id_notification = 'ntf-1';