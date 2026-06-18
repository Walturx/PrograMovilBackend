-- migrate:up
INSERT INTO reward_redemptions (id, user_id, reward_id, reservation_id, stars_spent, status, created_at) VALUES 
('rr1', 'u1', 'rw1', NULL, 5, 'completed', '2024-03-13'),
('rr2', 'u1', 'rw3', 'res1', 30, 'completed', '2024-03-20');

-- migrate:down
DELETE FROM reward_redemptions;