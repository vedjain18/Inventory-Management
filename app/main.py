from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import List, Optional
import logging
from datetime import datetime
import math

from .database import DatabaseManager
from .models import Product, Supplier, Category, StockMovement
from .schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductSummaryResponse,
    SupplierCreate, SupplierUpdate, SupplierResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    StockMovementCreate, StockMovementResponse,
    StockUpdateRequest, LowStockAlert, StockSummaryResponse,
    APIResponse, PaginatedResponse, PaginationParams
)
from .exceptions import (
    InventoryException, DatabaseConnectionError, ProductNotFoundError,
    InsufficientStockError, DuplicateProductCodeError
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Inventory Management API",
    description="A comprehensive inventory management system built with FastAPI and MySQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    global db_manager
    try:
        db_manager = DatabaseManager()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    global db_manager
    if db_manager:
        db_manager.close_connection()
        logger.info("Application shutdown complete")

def get_db_manager() -> DatabaseManager:
    """Dependency to get database manager instance"""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db_manager

@app.exception_handler(InventoryException)
async def inventory_exception_handler(request, exc: InventoryException):
    """Handle custom inventory exceptions"""
    status_codes = {
        "PRODUCT_NOT_FOUND": 404,
        "SUPPLIER_NOT_FOUND": 404,
        "CATEGORY_NOT_FOUND": 404,
        "INSUFFICIENT_STOCK": 400,
        "DUPLICATE_PRODUCT_CODE": 409,
        "VALIDATION_ERROR": 400,
        "DB_CONNECTION_ERROR": 500,
    }
    
    status_code = status_codes.get(exc.error_code, 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": str(exc),
            "error_code": "VALIDATION_ERROR"
        }
    )

@app.get("/", response_model=APIResponse)
async def root():
    """Welcome endpoint with API information"""
    return APIResponse(
        success=True,
        message="Welcome to Inventory Management API",
        data={
            "version": "1.0.0",
            "documentation": "/docs",
            "health_check": "/health"
        }
    )

@app.get("/health")
async def health_check(db: DatabaseManager = Depends(get_db_manager)):
    """Health check endpoint"""
    try:
        db._ensure_connection()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/suppliers/", response_model=APIResponse, status_code=201)
async def create_supplier(
    supplier_data: SupplierCreate,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Create a new supplier"""
    try:
        supplier = Supplier(**supplier_data.dict())
        supplier_id = db.create_supplier(supplier)
        
        return APIResponse(
            success=True,
            message="Supplier created successfully",
            data={"supplier_id": supplier_id}
        )
    except Exception as e:
        logger.error(f"Error creating supplier: {e}")
        raise e

@app.get("/suppliers/", response_model=PaginatedResponse)
async def get_suppliers(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get all suppliers with pagination"""
    try:
        suppliers, total = db.get_all_suppliers(page, size)
        pages = math.ceil(total / size)
        
        return PaginatedResponse(
            items=[supplier.to_dict() for supplier in suppliers],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error fetching suppliers: {e}")
        raise e

@app.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int = Path(..., gt=0, description="Supplier ID"),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get supplier by ID"""
    try:
        supplier = db.get_supplier_by_id(supplier_id)
        return SupplierResponse(**supplier.to_dict())
    except Exception as e:
        logger.error(f"Error fetching supplier {supplier_id}: {e}")
        raise e

@app.post("/categories/", response_model=APIResponse, status_code=201)
async def create_category(
    category_data: CategoryCreate,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Create a new category"""
    try:
        category = Category(**category_data.dict())
        category_id = db.create_category(category)
        
        return APIResponse(
            success=True,
            message="Category created successfully",
            data={"category_id": category_id}
        )
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise e

@app.get("/categories/", response_model=List[CategoryResponse])
async def get_categories(db: DatabaseManager = Depends(get_db_manager)):
    """Get all categories"""
    try:
        categories = db.get_all_categories()
        return [CategoryResponse(**category.to_dict()) for category in categories]
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise e

@app.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int = Path(..., gt=0, description="Category ID"),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get category by ID"""
    try:
        category = db.get_category_by_id(category_id)
        return CategoryResponse(**category.to_dict())
    except Exception as e:
        logger.error(f"Error fetching category {category_id}: {e}")
        raise e

@app.post("/products/", response_model=APIResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Create a new product"""
    try:
        product = Product(**product_data.dict())
        product_id = db.create_product(product)
        
        return APIResponse(
            success=True,
            message="Product created successfully",
            data={"product_id": product_id}
        )
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise e

@app.get("/products/", response_model=PaginatedResponse)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    low_stock_only: bool = Query(False, description="Show only low stock products"),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get all products with filters and pagination"""
    try:
        products, total = db.get_products_summary(
            page=page, 
            size=size,
            category_id=category_id,
            supplier_id=supplier_id,
            low_stock_only=low_stock_only
        )
        pages = math.ceil(total / size)
        
        return PaginatedResponse(
            items=products,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise e

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int = Path(..., gt=0, description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get product by ID"""
    try:
        product = db.get_product_by_id(product_id)
        return ProductResponse(**product.to_dict())
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        raise e

@app.put("/products/{product_id}/stock", response_model=APIResponse)
async def update_product_stock(
    product_id: int = Path(..., gt=0, description="Product ID"),
    stock_update: StockUpdateRequest = ...,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Update product stock with automatic stock movement creation"""
    try:
        product = db.get_product_by_id(product_id)
        
        if stock_update.quantity > 0:
            movement_type = "IN"
            quantity = stock_update.quantity
        else:
            movement_type = "OUT"
            quantity = abs(stock_update.quantity)
        
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            unit_price=product.unit_price,
            reference_number=stock_update.reference_number,
            notes=stock_update.notes,
            created_by="api_user"
        )
        
        movement_id = db.create_stock_movement(movement)
        
        updated_product = db.get_product_by_id(product_id)
        
        return APIResponse(
            success=True,
            message=f"Stock updated successfully. New stock: {updated_product.current_stock}",
            data={
                "movement_id": movement_id,
                "old_stock": product.current_stock,
                "new_stock": updated_product.current_stock,
                "change": stock_update.quantity
            }
        )
    except Exception as e:
        logger.error(f"Error updating stock for product {product_id}: {e}")
        raise e

@app.post("/stock-movements/", response_model=APIResponse, status_code=201)
async def create_stock_movement(
    movement_data: StockMovementCreate,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Create a new stock movement"""
    try:
        movement = StockMovement(**movement_data.dict())
        movement_id = db.create_stock_movement(movement)
        
        return APIResponse(
            success=True,
            message="Stock movement created successfully",
            data={"movement_id": movement_id}
        )
    except Exception as e:
        logger.error(f"Error creating stock movement: {e}")
        raise e

@app.get("/stock-movements/", response_model=PaginatedResponse)
async def get_stock_movements(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get stock movements with pagination"""
    try:
        movements, total = db.get_stock_movements(product_id, page, size)
        pages = math.ceil(total / size)
        
        return PaginatedResponse(
            items=movements,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        logger.error(f"Error fetching stock movements: {e}")
        raise e

@app.get("/analytics/low-stock-alerts", response_model=List[LowStockAlert])
async def get_low_stock_alerts(db: DatabaseManager = Depends(get_db_manager)):
    """Get products with low stock using database view"""
    try:
        alerts = db.get_low_stock_alerts()
        return [LowStockAlert(**alert) for alert in alerts]
    except Exception as e:
        logger.error(f"Error fetching low stock alerts: {e}")
        raise e

@app.get("/analytics/stock-summary", response_model=StockSummaryResponse)
async def get_stock_summary(db: DatabaseManager = Depends(get_db_manager)):
    """Get comprehensive stock summary with analytics"""
    try:
        summary = db.get_stock_summary()
        return StockSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error fetching stock summary: {e}")
        raise e

@app.get("/analytics/monthly-report")
async def get_monthly_report(
    year: int = Query(..., ge=2020, le=2030, description="Report year"),
    month: int = Query(..., ge=1, le=12, description="Report month"),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get monthly stock movement report"""
    try:
        report = db.get_monthly_stock_report(year, month)
        return {
            "success": True,
            "message": f"Monthly report for {year}-{month:02d}",
            "data": {
                "year": year,
                "month": month,
                "total_products": len(report),
                "movements": report
            }
        }
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        raise e

@app.get("/demo/sample-queries")
async def demo_sample_queries(db: DatabaseManager = Depends(get_db_manager)):
    """Demonstrate various SQL queries for interview purposes"""
    try:
        queries_demo = {
            "complex_join_query": """
            SELECT p.product_name, c.category_name, s.supplier_name,
                   p.current_stock, p.unit_price,
                   (p.current_stock * p.unit_price) as stock_value
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            WHERE p.is_active = 1
            ORDER BY stock_value DESC
            """,
            
            "subquery_example": """
            SELECT product_name, current_stock,
                   (SELECT AVG(current_stock) FROM products WHERE is_active = 1) as avg_stock
            FROM products 
            WHERE current_stock > (SELECT AVG(current_stock) FROM products WHERE is_active = 1)
            """,
            
            "aggregate_functions": """
            SELECT c.category_name,
                   COUNT(p.product_id) as product_count,
                   SUM(p.current_stock) as total_stock,
                   AVG(p.unit_price) as avg_price,
                   MIN(p.unit_price) as min_price,
                   MAX(p.unit_price) as max_price
            FROM categories c
            LEFT JOIN products p ON c.category_id = p.category_id AND p.is_active = 1
            GROUP BY c.category_id, c.category_name
            HAVING COUNT(p.product_id) > 0
            ORDER BY product_count DESC
            """,
            
            "case_when_example": """
            SELECT product_name,
                   current_stock,
                   minimum_stock,
                   CASE 
                       WHEN current_stock <= minimum_stock THEN 'URGENT: Reorder Now'
                       WHEN current_stock <= (minimum_stock * 1.5) THEN 'WARNING: Low Stock'
                       ELSE 'OK: Normal Stock'
                   END as stock_alert
            FROM products
            WHERE is_active = 1
            ORDER BY current_stock ASC
            """
        }
        
        return {
            "success": True,
            "message": "SQL query examples for interview demonstration",
            "data": {
                "note": "These queries demonstrate advanced SQL concepts",
                "concepts_covered": [
                    "Complex JOINs (LEFT JOIN with multiple tables)",
                    "Subqueries (correlated and non-correlated)",
                    "Aggregate functions (COUNT, SUM, AVG, MIN, MAX)",
                    "GROUP BY and HAVING clauses",
                    "CASE WHEN conditional logic",
                    "Window functions potential",
                    "Database views usage"
                ],
                "sample_queries": queries_demo
            }
        }
    except Exception as e:
        logger.error(f"Error in demo endpoint: {e}")
        raise e

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
