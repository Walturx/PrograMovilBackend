-- migrate:up
INSERT INTO rooms (id_room, hotel_id, room_type_id, room_number, floor, is_available, image_url) VALUES 
('r1', 'h1', 'rt1', '101', 1, 1, 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304'),
('r2', 'h1', 'rt2', '201', 2, 1, 'https://images.unsplash.com/photo-1590490360182-c33d57733427'),
('r3', 'h1', 'rt3', '301', 3, 0, 'https://images.unsplash.com/photo-1618773928121-c32242e63f39'),
('r4', 'h1', 'rt4', '102', 1, 1, 'https://images.unsplash.com/photo-1566665797739-1674de7a421a'),
('r5', 'h2', 'rt1', '101', 1, 1, 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304'),
('r6', 'h2', 'rt2', '202', 2, 0, 'https://images.unsplash.com/photo-1590490360182-c33d57733427'),
('r7', 'h3', 'rt1', '101', 1, 1, 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304'),
('r8', 'h3', 'rt3', '301', 3, 1, 'https://images.unsplash.com/photo-1618773928121-c32242e63f39'),
('r9', 'h4', 'rt2', '201', 2, 1, 'https://images.unsplash.com/photo-1590490360182-c33d57733427'),
('r10', 'h4', 'rt4', '102', 1, 1, 'https://images.unsplash.com/photo-1566665797739-1674de7a421a'),
('r11', 'h5', 'rt1', '101', 1, 1, 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304'),
('r12', 'h6', 'rt2', '201', 2, 0, 'https://images.unsplash.com/photo-1590490360182-c33d57733427');

-- migrate:down
DELETE FROM rooms WHERE id_room IN ('r1','r2','r3','r4','r5','r6','r7','r8','r9','r10','r11','r12');