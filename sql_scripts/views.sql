USE inventory_db;

CREATE VIEW low_stock_alert AS
SELECT 
    p.product_id,
    p.product_name,
    p.product_code,
    c.category_name,
    s.supplier_name,
    p.current_stock,
    p.minimum_stock,
    (p.minimum_stock - p.current_stock) as shortage_quantity,
    p.unit_price,
    (p.unit_price * (p.minimum_stock - p.current_stock)) as required_investment
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
WHERE p.current_stock <= p.minimum_stock 
AND p.is_active = TRUE
ORDER BY shortage_quantity DESC;

CREATE VIEW product_summary AS
SELECT 
    p.product_id,
    p.product_name,
    p.product_code,
    c.category_name,
    s.supplier_name,
    s.contact_person as supplier_contact,
    p.unit_price,
    p.current_stock,
    p.minimum_stock,
    p.maximum_stock,
    (p.current_stock * p.unit_price) as stock_value,
    CASE 
        WHEN p.current_stock <= p.minimum_stock THEN 'Low Stock'
        WHEN p.current_stock >= p.maximum_stock THEN 'Overstock'
        ELSE 'Normal'
    END as stock_status,
    p.is_active,
    p.created_at,
    p.updated_at
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id;

CREATE VIEW monthly_stock_summary AS
SELECT 
    DATE_FORMAT(sm.movement_date, '%Y-%m') as month_year,
    p.product_name,
    c.category_name,
    SUM(CASE WHEN sm.movement_type = 'IN' THEN sm.quantity ELSE 0 END) as total_in,
    SUM(CASE WHEN sm.movement_type = 'OUT' THEN sm.quantity ELSE 0 END) as total_out,
    SUM(CASE WHEN sm.movement_type = 'ADJUSTMENT' THEN sm.quantity ELSE 0 END) as total_adjustments,
    COUNT(*) as total_movements
FROM stock_movements sm
JOIN products p ON sm.product_id = p.product_id
LEFT JOIN categories c ON p.category_id = c.category_id
GROUP BY DATE_FORMAT(sm.movement_date, '%Y-%m'), p.product_id
ORDER BY month_year DESC, p.product_name;

SELECT 'Views created successfully!' as message;
