class InventoryException(Exception):
    """Base exception class for inventory-related errors"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class DatabaseConnectionError(InventoryException):
    """Raised when database connection fails"""
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(message, "DB_CONNECTION_ERROR")

class ProductNotFoundError(InventoryException):
    """Raised when a product is not found"""
    def __init__(self, product_id: int = None, product_code: str = None):
        if product_id:
            message = f"Product with ID {product_id} not found"
        elif product_code:
            message = f"Product with code {product_code} not found"
        else:
            message = "Product not found"
        super().__init__(message, "PRODUCT_NOT_FOUND")

class InsufficientStockError(InventoryException):
    """Raised when trying to reduce stock below available quantity"""
    def __init__(self, product_name: str, available: int, requested: int):
        message = f"Insufficient stock for {product_name}. Available: {available}, Requested: {requested}"
        super().__init__(message, "INSUFFICIENT_STOCK")

class DuplicateProductCodeError(InventoryException):
    """Raised when trying to create a product with existing product code"""
    def __init__(self, product_code: str):
        message = f"Product with code {product_code} already exists"
        super().__init__(message, "DUPLICATE_PRODUCT_CODE")

class InvalidStockQuantityError(InventoryException):
    """Raised when stock quantity is invalid"""
    def __init__(self, quantity: int):
        message = f"Invalid stock quantity: {quantity}. Quantity must be positive"
        super().__init__(message, "INVALID_STOCK_QUANTITY")

class SupplierNotFoundError(InventoryException):
    """Raised when a supplier is not found"""
    def __init__(self, supplier_id: int):
        message = f"Supplier with ID {supplier_id} not found"
        super().__init__(message, "SUPPLIER_NOT_FOUND")

class CategoryNotFoundError(InventoryException):
    """Raised when a category is not found"""
    def __init__(self, category_id: int):
        message = f"Category with ID {category_id} not found"
        super().__init__(message, "CATEGORY_NOT_FOUND")

class ValidationError(InventoryException):
    """Raised when data validation fails"""
    def __init__(self, field: str, value: str, reason: str):
        message = f"Validation error for {field} with value '{value}': {reason}"
        super().__init__(message, "VALIDATION_ERROR")
