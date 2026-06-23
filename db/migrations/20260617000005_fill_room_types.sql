-- migrate:up
INSERT INTO room_types (id_room_type, name, description, base_price, capacity) VALUES 
('rt1', 'Estándar', 'Habitación cómoda con cama doble, baño privado y TV.', 120.00, 2),
('rt2', 'Suite Deluxe', 'Suite amplia con sala de estar, minibar y vista panorámica.', 280.00, 3),
('rt3', 'Junior Suite', 'Habitación premium con escritorio, sofá y balcón privado.', 200.00, 2),
('rt4', 'Familiar', 'Habitación espaciosa con dos camas dobles ideal para familias.', 350.00, 5);

-- migrate:down
DELETE FROM room_types WHERE id_room_type IN ('rt1', 'rt2', 'rt3', 'rt4');