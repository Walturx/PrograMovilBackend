-- migrate:up
INSERT INTO reviews (id_review, reservation_id, user_id, hotel_id, rating, comment, created_at) VALUES 
('rev1', 'res1', 'u1', 'h1', 5, 'Excelente hotel, las vistas son increíbles y el servicio de primera.', '2026-05-14'),
('rev2', 'res2', 'u1', 'h1', 4, 'Muy buena experiencia, solo el check-in fue un poco lento.', '2026-04-20'),
('rev3', NULL, 'u1', 'h2', 5, 'El mejor hotel boutique que he visitado. Totalmente recomendado.', '2026-03-15'),
('rev4', NULL, 'u1', 'h3', 4, 'Ubicación perfecta en Miraflores, cerca de todo.', '2026-04-10'),
('rev5', NULL, 'u1', 'h4', 5, 'El spa andino es una experiencia única. Hotel hermoso.', '2026-05-01');

-- migrate:down
DELETE FROM reviews WHERE id_review IN ('rev1', 'rev2', 'rev3', 'rev4', 'rev5');