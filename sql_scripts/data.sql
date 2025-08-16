USE inventory_db;

INSERT INTO suppliers (supplier_name, contact_person, email, phone, address) VALUES
('TechWorld Suppliers', 'John Smith', 'john@techworld.com', '+1-555-0101', '123 Tech Street, Silicon Valley, CA'),
('Global Electronics', 'Sarah Johnson', 'sarah@globalelec.com', '+1-555-0102', '456 Circuit Ave, Austin, TX'),
('Office Solutions Ltd', 'Mike Wilson', 'mike@officesol.com', '+1-555-0103', '789 Business Blvd, New York, NY'),
('Mobile Distributors', 'Lisa Chen', 'lisa@mobiledist.com', '+1-555-0104', '321 Mobile Lane, Los Angeles, CA');

INSERT INTO categories (category_name, description) VALUES
('Laptops', 'Portable computers for personal and business use'),
('Smartphones', 'Mobile phones with advanced computing capabilities'),
('Tablets', 'Portable touchscreen computers'),
('Accessories', 'Computer and mobile device accessories'),
('Office Equipment', 'General office and business equipment');

INSERT INTO products (product_name, product_code, category_id, supplier_id, unit_price, current_stock, minimum_stock, maximum_stock, description) VALUES
('MacBook Pro 16"', 'MBP16-001', 1, 1, 2499.99, 15, 5, 50, 'High-performance laptop with M2 chip'),
('Dell XPS 13', 'DELL-XPS13', 1, 1, 1299.99, 8, 10, 30, 'Ultra-portable business laptop'),
('iPhone 15 Pro', 'IPH15-PRO', 2, 2, 999.99, 25, 15, 100, 'Latest iPhone with advanced camera system'),
('Samsung Galaxy S24', 'SAM-S24', 2, 2, 899.99, 12, 10, 75, 'Android smartphone with AI features'),
('iPad Air', 'IPAD-AIR', 3, 1, 599.99, 20, 8, 40, 'Versatile tablet for work and creativity'),
('Surface Pro 9', 'SUR-PRO9', 3, 3, 1099.99, 6, 10, 25, 'Windows tablet with laptop capabilities'),
('Wireless Mouse', 'WM-001', 4, 3, 29.99, 50, 20, 200, 'Ergonomic wireless mouse'),
('USB-C Hub', 'HUB-USBC', 4, 4, 79.99, 30, 15, 100, 'Multi-port USB-C connectivity hub'),
('Bluetooth Headphones', 'BT-HP-001', 4, 2, 199.99, 18, 12, 60, 'Noise-cancelling wireless headphones'),
('Office Printer', 'PRT-OFF-01', 5, 3, 299.99, 5, 8, 20, 'Multi-function office printer');

INSERT INTO stock_movements (product_id, movement_type, quantity, unit_price, reference_number, notes) VALUES
(1, 'IN', 20, 2499.99, 'PO-2024-001', 'Initial stock purchase'),
(2, 'IN', 15, 1299.99, 'PO-2024-002', 'Initial stock purchase'),
(3, 'IN', 40, 999.99, 'PO-2024-003', 'Initial stock purchase'),
(4, 'IN', 25, 899.99, 'PO-2024-004', 'Initial stock purchase'),
(5, 'IN', 30, 599.99, 'PO-2024-005', 'Initial stock purchase'),
(1, 'OUT', 5, 2499.99, 'SO-2024-001', 'Sale to corporate client'),
(2, 'OUT', 7, 1299.99, 'SO-2024-002', 'Online sales'),
(3, 'OUT', 15, 999.99, 'SO-2024-003', 'Retail store sales'),
(4, 'OUT', 13, 899.99, 'SO-2024-004', 'Bulk order fulfillment'),
(5, 'OUT', 10, 599.99, 'SO-2024-005', 'Education sector sales');

UPDATE products SET current_stock = (
    SELECT COALESCE(
        (SELECT SUM(CASE 
            WHEN movement_type = 'IN' THEN quantity
            WHEN movement_type = 'OUT' THEN -quantity
            WHEN movement_type = 'ADJUSTMENT' THEN quantity
        END)
        FROM stock_movements 
        WHERE stock_movements.product_id = products.product_id), 0
    )
);

SELECT 'Sample data inserted successfully!' as message;

SELECT 'Suppliers' as table_name, COUNT(*) as record_count FROM suppliers
UNION ALL
SELECT 'Categories', COUNT(*) FROM categories
UNION ALL  
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Stock Movements', COUNT(*) FROM stock_movements;
