-- migrate:up
INSERT INTO hotel_amenities (hotel_id, amenity_id) VALUES 
('h1', 'am-wifi'),
('h1', 'am-pool');

-- migrate:down
DELETE FROM hotel_amenities WHERE hotel_id = 'h1';