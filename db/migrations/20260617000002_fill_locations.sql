-- migrate:up
INSERT INTO locations (id_location, country, city, state) VALUES 
('loc1', 'Perú', 'Lima', 'Lima'),
('loc2', 'Perú', 'Lima', 'Lima boutique'),
('loc3', 'Perú', 'Lima', 'Miraflores'),
('loc4', 'Perú', 'Cusco', 'Cusco Centro'),
('loc5', 'Perú', 'Arequipa', 'Arequipa Centro');

-- migrate:down
DELETE FROM locations WHERE id_location IN ('loc1', 'loc2', 'loc3', 'loc4', 'loc5');