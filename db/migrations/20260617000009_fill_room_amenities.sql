-- migrate:up
INSERT INTO room_amenities (room_id, amenity_id) VALUES 
('r1', 'am-wifi');

-- migrate:down
DELETE FROM room_amenities WHERE room_id = 'r1';