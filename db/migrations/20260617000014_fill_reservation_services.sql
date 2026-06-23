-- migrate:up
INSERT INTO reservation_services (id_reservation_service, reservation_id, service_id, quantity, subtotal) VALUES 
('res-srv-1', 'res1', 'srv-spa', 1, 45.00);

-- migrate:down
DELETE FROM reservation_services WHERE id_reservation_service = 'res-srv-1';