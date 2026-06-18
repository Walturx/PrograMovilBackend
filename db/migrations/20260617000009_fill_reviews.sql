-- migrate:up
INSERT INTO reviews (id, reservation_id, user_id, hotel_id, rating, comment, created_at, user_name) VALUES 
('rev1', 'res1', 'u1', 'h1', 5, 'Excelente hotel, las vistas son increíbles y el servicio de primera.', '2026-05-14', 'Carlos Mendoza'),
('rev2', 'res2', 'u1', 'h1', 4, 'Muy buena experiencia, solo el check-in fue un poco lento.', '2026-04-20', 'María López'),
('rev3', NULL, 'u1', 'h2', 5, 'El mejor hotel boutique que he visitado. Totalmente recomendado.', '2026-03-15', 'Ana García');

-- migrate:down
DELETE FROM reviews;