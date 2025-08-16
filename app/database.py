import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

from .models import Product, Supplier, Category, StockMovement
from .exceptions import (
    DatabaseConnectionError, ProductNotFoundError, InsufficientStockError,
    DuplicateProductCodeError, SupplierNotFoundError, CategoryNotFoundError
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database manager class with comprehensive CRUD operations and advanced SQL features.
    Demonstrates proper connection handling, prepared statements, and error management.
    """
    
    def __init__(self):
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection with proper error handling"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'inventory_db'),
                autocommit=False,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info("Successfully connected to MySQL database")
        except Error as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        try:
            if not self.connection or not self.connection.is_connected():
                self._connect()
        except Error as e:
            raise DatabaseConnectionError(f"Connection check failed: {e}")
    
    def _execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> List[Dict[str, Any]]:
        """Execute query with proper error handling and return results"""
        self._ensure_connection()
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                return cursor.fetchall()
            else:
                self.connection.commit()
                return [{"affected_rows": cursor.rowcount, "last_insert_id": cursor.lastrowid}]
                
        except Error as e:
            self.connection.rollback()
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query execution failed: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def create_supplier(self, supplier: Supplier) -> int:
        """Create a new supplier and return the ID"""
        supplier.validate()
        
        query = """
        INSERT INTO suppliers (supplier_name, contact_person, email, phone, address)
        VALUES (%s, %s, %s, %s, %s)
        """
        params = (supplier.supplier_name, supplier.contact_person, 
                 supplier.email, supplier.phone, supplier.address)
        
        result = self._execute_query(query, params, fetch=False)
        return result[0]["last_insert_id"]
    
    def get_supplier_by_id(self, supplier_id: int) -> Supplier:
        """Get supplier by ID"""
        query = "SELECT * FROM suppliers WHERE supplier_id = %s"
        result = self._execute_query(query, (supplier_id,))
        
        if not result:
            raise SupplierNotFoundError(supplier_id)
        
        return Supplier(**result[0])
    
    def get_all_suppliers(self, page: int = 1, size: int = 10) -> Tuple[List[Supplier], int]:
        """Get all suppliers with pagination"""
        offset = (page - 1) * size
        
        count_query = "SELECT COUNT(*) as total FROM suppliers"
        total_result = self._execute_query(count_query)
        total = total_result[0]['total']
        
        query = "SELECT * FROM suppliers ORDER BY supplier_name LIMIT %s OFFSET %s"
        results = self._execute_query(query, (size, offset))
        
        suppliers = [Supplier(**row) for row in results]
        return suppliers, total
    
    def create_category(self, category: Category) -> int:
        """Create a new category and return the ID"""
        category.validate()
        
        query = """
        INSERT INTO categories (category_name, description)
        VALUES (%s, %s)
        """
        params = (category.category_name, category.description)
        
        result = self._execute_query(query, params, fetch=False)
        return result[0]["last_insert_id"]
    
    def get_category_by_id(self, category_id: int) -> Category:
        """Get category by ID"""
        query = "SELECT * FROM categories WHERE category_id = %s"
        result = self._execute_query(query, (category_id,))
        
        if not result:
            raise CategoryNotFoundError(category_id)
        
        return Category(**result[0])
    
    def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        query = "SELECT * FROM categories ORDER BY category_name"
        results = self._execute_query(query)
        return [Category(**row) for row in results]
    
    def create_product(self, product: Product) -> int:
        """Create a new product with duplicate code checking"""
        product.validate()
        
        check_query = """
        SELECT COUNT(*) as count FROM products 
        WHERE product_code = %s AND product_id != COALESCE(%s, 0)
        """
        result = self._execute_query(check_query, (product.product_code, None))
        
        if result[0]['count'] > 0:
            raise DuplicateProductCodeError(product.product_code)
        
        query = """
        INSERT INTO products 
        (product_name, product_code, category_id, supplier_id, unit_price, 
         current_stock, minimum_stock, maximum_stock, description, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (product.product_name, product.product_code, product.category_id,
                 product.supplier_id, product.unit_price, product.current_stock,
                 product.minimum_stock, product.maximum_stock, product.description,
                 product.is_active)
        
        result = self._execute_query(query, params, fetch=False)
        return result[0]["last_insert_id"]
    
    def get_product_by_id(self, product_id: int) -> Product:
        """Get product by ID with related data using JOIN"""
        query = """
        SELECT p.*, c.category_name, s.supplier_name 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE p.product_id = %s
        """
        result = self._execute_query(query, (product_id,))
        
        if not result:
            raise ProductNotFoundError(product_id)
        
        row = result[0]
        return Product(
            product_id=row['product_id'],
            product_name=row['product_name'],
            product_code=row['product_code'],
            category_id=row['category_id'],
            supplier_id=row['supplier_id'],
            unit_price=row['unit_price'],
            current_stock=row['current_stock'],
            minimum_stock=row['minimum_stock'],
            maximum_stock=row['maximum_stock'],
            description=row['description'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def get_products_summary(self, page: int = 1, size: int = 10, 
                            category_id: int = None, supplier_id: int = None,
                            low_stock_only: bool = False) -> Tuple[List[Dict], int]:
        """Get products with complete information using complex JOIN and WHERE clauses"""
        conditions = ["p.is_active = 1"]
        params = []
        
        if category_id:
            conditions.append("p.category_id = %s")
            params.append(category_id)
        
        if supplier_id:
            conditions.append("p.supplier_id = %s")
            params.append(supplier_id)
        
        if low_stock_only:
            conditions.append("p.current_stock <= p.minimum_stock")
        
        where_clause = " AND ".join(conditions)
        
        count_query = f"""
        SELECT COUNT(*) as total 
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE {where_clause}
        """
        
        total_result = self._execute_query(count_query, tuple(params))
        total = total_result[0]['total']
        
        offset = (page - 1) * size
        query = f"""
        SELECT p.*, c.category_name, s.supplier_name, s.contact_person as supplier_contact,
               (p.current_stock * p.unit_price) as stock_value,
               CASE 
                   WHEN p.current_stock <= p.minimum_stock THEN 'Low Stock'
                   WHEN p.current_stock >= p.maximum_stock THEN 'Overstock'
                   ELSE 'Normal'
               END as stock_status
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
        WHERE {where_clause}
        ORDER BY p.product_name
        LIMIT %s OFFSET %s
        """
        
        params.extend([size, offset])
        results = self._execute_query(query, tuple(params))
        
        return results, total
    
    def update_product_stock(self, product_id: int, new_stock: int) -> bool:
        """Update product stock with validation"""

        product = self.get_product_by_id(product_id)
        
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        
        query = """
        UPDATE products 
        SET current_stock = %s, updated_at = CURRENT_TIMESTAMP
        WHERE product_id = %s
        """
        
        self._execute_query(query, (new_stock, product_id), fetch=False)
        return True
    
    # STOCK MOVEMENT OPERATIONS
    def create_stock_movement(self, movement: StockMovement) -> int:
        """Create stock movement and update product stock atomically"""
        movement.validate()
        
        try:
            self.connection.autocommit = False
            
            product = self.get_product_by_id(movement.product_id)
            stock_change = movement.get_stock_change()
            new_stock = product.current_stock + stock_change
            
            if new_stock < 0:
                raise InsufficientStockError(
                    product.product_name, 
                    product.current_stock, 
                    abs(stock_change)
                )
            
            movement_query = """
            INSERT INTO stock_movements 
            (product_id, movement_type, quantity, unit_price, reference_number, notes, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            movement_params = (
                movement.product_id, movement.movement_type, movement.quantity,
                movement.unit_price, movement.reference_number, movement.notes,
                movement.created_by
            )
            
            result = self._execute_query(movement_query, movement_params, fetch=False)
            movement_id = result[0]["last_insert_id"]
            
            self.update_product_stock(movement.product_id, new_stock)
            
            self.connection.commit()
            return movement_id
            
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            self.connection.autocommit = True
    
    def get_stock_movements(self, product_id: int = None, page: int = 1, size: int = 10) -> Tuple[List[Dict], int]:
        """Get stock movements with optional product filter"""
        conditions = []
        params = []
        
        if product_id:
            conditions.append("sm.product_id = %s")
            params.append(product_id)
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        count_query = f"SELECT COUNT(*) as total FROM stock_movements sm {where_clause}"
        total_result = self._execute_query(count_query, tuple(params))
        total = total_result[0]['total']
        
        offset = (page - 1) * size
        query = f"""
        SELECT sm.*, p.product_name, p.product_code
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.product_id
        {where_clause}
        ORDER BY sm.movement_date DESC
        LIMIT %s OFFSET %s
        """
        
        params.extend([size, offset])
        results = self._execute_query(query, tuple(params))
        
        return results, total
    
    def get_low_stock_alerts(self) -> List[Dict]:
        """Get low stock alerts using database VIEW"""
        query = "SELECT * FROM low_stock_alert ORDER BY shortage_quantity DESC"
        return self._execute_query(query)
    
    def get_stock_summary(self) -> Dict[str, Any]:
        """Get comprehensive stock summary using aggregation functions"""
        query = """
        SELECT 
            COUNT(*) as total_products,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_products,
            SUM(CASE WHEN current_stock <= minimum_stock AND is_active = 1 THEN 1 ELSE 0 END) as low_stock_products,
            SUM(CASE WHEN current_stock >= maximum_stock AND is_active = 1 THEN 1 ELSE 0 END) as overstock_products,
            SUM(current_stock * unit_price) as total_stock_value,
            (SELECT COUNT(DISTINCT category_id) FROM products WHERE is_active = 1) as categories_count,
            (SELECT COUNT(*) FROM suppliers) as suppliers_count
        FROM products
        """
        result = self._execute_query(query)
        return result[0] if result else {}
    
    def get_monthly_stock_report(self, year: int, month: int) -> List[Dict]:
        """Get monthly stock movement report using date functions and GROUP BY"""
        query = """
        SELECT 
            p.product_name,
            c.category_name,
            SUM(CASE WHEN sm.movement_type = 'IN' THEN sm.quantity ELSE 0 END) as total_in,
            SUM(CASE WHEN sm.movement_type = 'OUT' THEN sm.quantity ELSE 0 END) as total_out,
            SUM(CASE WHEN sm.movement_type = 'ADJUSTMENT' THEN sm.quantity ELSE 0 END) as total_adjustments,
            COUNT(*) as total_movements
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.product_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE YEAR(sm.movement_date) = %s AND MONTH(sm.movement_date) = %s
        GROUP BY p.product_id, p.product_name, c.category_name
        HAVING COUNT(*) > 0
        ORDER BY total_movements DESC
        """
        
        return self._execute_query(query, (year, month))
    
    def close_connection(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
