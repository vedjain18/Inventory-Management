from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum

class MovementType(str, Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"

class StockStatus(str, Enum):
    LOW_STOCK = "Low Stock"
    NORMAL = "Normal"
    OVERSTOCK = "Overstock"

class SupplierBase(BaseModel):
    supplier_name: str = Field(..., min_length=1, max_length=100, description="Supplier name")
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person name")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    address: Optional[str] = Field(None, description="Supplier address")
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

class SupplierResponse(SupplierBase):
    supplier_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=50, description="Category name")
    description: Optional[str] = Field(None, description="Category description")

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    category_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=100, description="Product name")
    product_code: str = Field(..., min_length=1, max_length=50, description="Unique product code")
    category_id: Optional[int] = Field(None, description="Category ID")
    supplier_id: Optional[int] = Field(None, description="Supplier ID")
    unit_price: Decimal = Field(..., gt=0, description="Unit price must be greater than 0")
    current_stock: int = Field(0, ge=0, description="Current stock quantity")
    minimum_stock: int = Field(10, ge=0, description="Minimum stock threshold")
    maximum_stock: int = Field(1000, gt=0, description="Maximum stock capacity")
    description: Optional[str] = Field(None, description="Product description")
    is_active: bool = Field(True, description="Product active status")
    
    @validator('maximum_stock')
    def validate_max_stock(cls, v, values):
        if 'minimum_stock' in values and v <= values['minimum_stock']:
            raise ValueError('Maximum stock must be greater than minimum stock')
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=100)
    product_code: Optional[str] = Field(None, min_length=1, max_length=50)
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    unit_price: Optional[Decimal] = Field(None, gt=0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    maximum_stock: Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    product_id: int
    stock_status: StockStatus
    stock_value: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProductSummaryResponse(ProductResponse):
    category_name: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None

class StockMovementBase(BaseModel):
    product_id: int = Field(..., description="Product ID")
    movement_type: MovementType = Field(..., description="Type of stock movement")
    quantity: int = Field(..., gt=0, description="Quantity moved")
    unit_price: Optional[Decimal] = Field(None, gt=0, description="Unit price for the movement")
    reference_number: Optional[str] = Field(None, max_length=50, description="Reference number")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_by: str = Field("system", max_length=50, description="User who created the movement")

class StockMovementCreate(StockMovementBase):
    pass

class StockMovementResponse(StockMovementBase):
    movement_id: int
    stock_change: int
    movement_date: datetime
    
    class Config:
        from_attributes = True
        
class StockUpdateRequest(BaseModel):
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., description="Quantity to add (positive) or remove (negative)")
    reference_number: Optional[str] = Field(None, description="Reference number")
    notes: Optional[str] = Field(None, description="Notes for the movement")

class LowStockAlert(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    category_name: Optional[str]
    supplier_name: Optional[str]
    current_stock: int
    minimum_stock: int
    shortage_quantity: int
    unit_price: Decimal
    required_investment: Decimal
    
    class Config:
        from_attributes = True

class StockSummaryResponse(BaseModel):
    total_products: int
    active_products: int
    low_stock_products: int
    overstock_products: int
    total_stock_value: Decimal
    categories_count: int
    suppliers_count: int

class APIResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None
    error_code: Optional[str] = None

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Number of items per page")
    
class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int
