-- migrate:up
INSERT INTO reservations (id, user_id, room_id, check_in, check_out, total_price, status, adults, children, special_requests, created_at) VALUES 
('res1', 'u1', 'r2', '2026-05-10', '2026-05-13', 450.00, 'completed', 2, 1, 'Vista al mar', '2026-05-01'),
('res2', 'u1', 'r8', '2026-05-20', '2026-05-25', 800.00, 'pending', 2, 0, 'Cama extra', '2026-05-15');

-- migrate:down
DELETE FROM reservations;