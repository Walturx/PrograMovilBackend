-- migrate:up
INSERT INTO hotels (id_hotel, location_id, name, description, stars, phone, email, cover_image_url, is_active) VALUES 
('h1', 'loc1', 'Hotel Paradise', 'Un lujoso hotel frente al mar con vistas espectaculares y servicio de primera clase.', 5, '+51 1 234 5678', 'contacto@hotelparadise.com', 'https://images.unsplash.com/photo-1566073771259-6a8506099945', 1),
('h2', 'loc2', 'Ocean View Hotel', 'Hotel boutique con diseño moderno y acceso directo a la playa.', 4, '+51 1 345 6789', 'reservas@oceanview.com', 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa', 1),
('h3', 'loc3', 'Grand Lima Hotel', 'Ubicado en el corazón de Miraflores, ideal para viajes de negocios y turismo.', 4, '+51 1 456 7890', 'info@grandlima.com', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb', 1),
('h4', 'loc4', 'Cusco Imperial', 'Hotel colonial restaurado con vistas a la Plaza de Armas y spa andino.', 5, '+51 84 567 890', 'reservas@cuscoimperial.com', 'https://images.unsplash.com/photo-1445019980597-93fa8acb246c', 1),
('h5', 'loc5', 'Arequipa Plaza Hotel', 'Hotel familiar con piscina temperada y restaurante de comida arequipeña.', 3, '+51 54 678 901', 'contacto@arequipaplaza.com', 'https://images.unsplash.com/photo-1564501049412-61c2a3083791', 1),
('h6', 'loc1', 'Sunset Beach Resort', 'Resort todo incluido con actividades acuáticas y entretenimiento nocturno.', 4, '+51 1 789 0123', 'info@sunsetbeach.com', 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4', 0);

-- migrate:down
DELETE FROM hotels WHERE id_hotel IN ('h1', 'h2', 'h3', 'h4', 'h5', 'h6');