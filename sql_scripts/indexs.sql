USE inventory_db;

CREATE INDEX idx_product_name ON products(product_name);
CREATE INDEX idx_product_code ON products(product_code);
CREATE INDEX idx_category_id ON products(category_id);
CREATE INDEX idx_supplier_id ON products(supplier_id);
CREATE INDEX idx_stock_status ON products(current_stock, minimum_stock);
CREATE INDEX idx_active_products ON products(is_active);

CREATE INDEX idx_category_stock ON products(category_id, current_stock);
CREATE INDEX idx_supplier_active ON products(supplier_id, is_active);

CREATE INDEX idx_product_movement ON stock_movements(product_id, movement_date);
CREATE INDEX idx_movement_type ON stock_movements(movement_type);
CREATE INDEX idx_movement_date ON stock_movements(movement_date);
CREATE INDEX idx_reference_number ON stock_movements(reference_number);

CREATE INDEX idx_supplier_name ON suppliers(supplier_name);
CREATE INDEX idx_supplier_email ON suppliers(email);

CREATE INDEX idx_category_name ON categories(category_name);

SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE,
    INDEX_TYPE
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'inventory_db'
ORDER BY TABLE_NAME, INDEX_NAME;

SELECT 'Indexes created successfully!' as message;
