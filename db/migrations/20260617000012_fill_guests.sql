-- migrate:up
INSERT INTO guests (id_guest, reservation_id, name, lastname, document_type, document_number, nationality) VALUES 
('gst-1', 'res1', 'María', 'López', 'DNI', '44556677', 'Peruana');

-- migrate:down
DELETE FROM guests WHERE id_guest = 'gst-1';