-- migrate:up
INSERT INTO rooms (id, hotel_id, room_type_id, room_number, floor, is_available, image_url) VALUES 
('r1', 'h1', 'rt1', '101', 1, 1, 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304'),
('r2', 'h1', 'rt2', '201', 2, 1, 'https://images.unsplash.com/photo-1590490360182-c33d955735ed'),
('r3', 'h1', 'rt3', '301', 3, 0, 'https://images.unsplash.com/photo-1618773928121-c32242e63f39'),
('r5', 'h2', 'rt1', '101', 1, 1, 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b'),
('r6', 'h2', 'rt2', '201', 2, 0, 'https://images.unsplash.com/photo-1566665797739-1674de7a421a'),
('r7', 'h3', 'rt1', '101', 1, 1, 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304'),
('r8', 'h3', 'rt3', '301', 3, 1, 'https://images.unsplash.com/photo-1618773928121-c32242e63f39'),
('r9', 'h4', 'rt2', '201', 2, 1, 'https://images.unsplash.com/photo-1590490360182-c33d955735ed');
-- migrate:down
DELETE FROM rooms;