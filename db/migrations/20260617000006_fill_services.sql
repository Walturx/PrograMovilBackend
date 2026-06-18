-- migrate:up
INSERT INTO additional_services (id, hotel_id, name, price, description) VALUES 
('s1', 'h1', 'Desayuno Buffet', 25.00, 'Desayuno completo con opciones internacionales y locales.'),
('s2', 'h1', 'Spa & Masajes', 80.00, 'Sesión de relajación con masaje corporal completo.'),
('s3', 'h1', 'Traslado Aeropuerto', 45.00, 'Servicio de transporte privado al aeropuerto.'),
('s4', 'h1', 'Lavandería Express', 15.00, 'Servicio de lavado y planchado en 4 horas.'),
('s5', 'h2', 'Desayuno Continental', 18.00, 'Desayuno ligero con café, jugos y panes.'),
('s6', 'h2', 'Tour en Bote', 60.00, 'Paseo en bote por la costa con guía turístico.'),
('s7', 'h3', 'Room Service 24h', 10.00, 'Servicio de comida a la habitación disponible las 24 horas.'),
('s8', 'h3', 'Gimnasio Premium', 0.00, 'Acceso gratuito al gimnasio equipado con máquinas modernas.');
-- migrate:down
DELETE FROM additional_services;