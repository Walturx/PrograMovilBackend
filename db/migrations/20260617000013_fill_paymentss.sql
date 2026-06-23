-- migrate:up
INSERT INTO payments (id_payment, reservation_id, amount, method, status, paid_at, transaction_id) VALUES 
('pay-1', 'res1', 406.00, 'Tarjeta de Crédito', 'Aprobado', '2026-06-22 12:05:00', 'TXN-9988776655');

-- migrate:down
DELETE FROM payments WHERE id_payment = 'pay-1';