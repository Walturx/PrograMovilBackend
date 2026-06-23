-- migrate:up
INSERT INTO amenities (id_amenity, name, icon, category) VALUES 
('am-wifi', 'Wi-Fi Gratis', 'wifi-icon', 'Conectividad'),
('am-pool', 'Piscina Temperada', 'pool-icon', 'Instalaciones');

-- migrate:down
DELETE FROM amenities WHERE id_amenity IN ('am-wifi', 'am-pool');