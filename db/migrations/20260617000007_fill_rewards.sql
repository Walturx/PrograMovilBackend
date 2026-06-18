-- migrate:up
INSERT INTO rewards (id, name, description, stars_cost, type, is_active) VALUES 
('rw1', 'Helado Premium', 'Helado gratis', 5, 'food', 1),
('rw2', 'Chicha Gratis', 'Bebida gratis', 4, 'drink', 1),
('rw3', '1 Noche Gratis', 'Hospedaje gratis', 30, 'hotel', 1);
-- migrate:down
DELETE FROM rewards;