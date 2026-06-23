-- migrate:up
INSERT INTO services (id_service, hotel_id, name, price, description) VALUES 
('srv-spa', 'h1', 'Masaje de Piedras Calientes', 45.00, 'Sesión de 60 minutos en el spa del hotel.');

-- migrate:down
DELETE FROM services WHERE id_service = 'srv-spa';