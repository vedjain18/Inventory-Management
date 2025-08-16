from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Supplier:
    """Supplier model with business logic methods"""
    supplier_id: Optional[int] = None
    supplier_name: str = ""
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Validate supplier data"""
        if not self.supplier_name or len(self.supplier_name.strip()) == 0:
            raise ValueError("Supplier name is required")
        
        if self.email and "@" not in self.email:
            raise ValueError("Invalid email format")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert supplier object to dictionary"""
        return {
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class Category:
    """Category model with validation methods"""
    category_id: Optional[int] = None
    category_name: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Validate category data"""
        if not self.category_name or len(self.category_name.strip()) == 0:
            raise ValueError("Category name is required")
        
        if len(self.category_name) > 50:
            raise ValueError("Category name must be 50 characters or less")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert category object to dictionary"""
        return {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class Product:
    """Product model with comprehensive business logic"""
    product_id: Optional[int] = None
    product_name: str = ""
    product_code: str = ""
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    unit_price: Decimal = Decimal('0.00')
    current_stock: int = 0
    minimum_stock: int = 10
    maximum_stock: int = 1000
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Validate product data"""
        if not self.product_name or len(self.product_name.strip()) == 0:
            raise ValueError("Product name is required")
        
        if not self.product_code or len(self.product_code.strip()) == 0:
            raise ValueError("Product code is required")
        
        if self.unit_price <= 0:
            raise ValueError("Unit price must be greater than 0")
        
        if self.current_stock < 0:
            raise ValueError("Current stock cannot be negative")
        
        if self.minimum_stock < 0:
            raise ValueError("Minimum stock cannot be negative")
        
        if self.maximum_stock <= self.minimum_stock:
            raise ValueError("Maximum stock must be greater than minimum stock")
        
        return True
    
    def is_low_stock(self) -> bool:
        """Check if product stock is below minimum threshold"""
        return self.current_stock <= self.minimum_stock
    
    def is_overstock(self) -> bool:
        """Check if product stock exceeds maximum threshold"""
        return self.current_stock >= self.maximum_stock
    
    def get_stock_status(self) -> str:
        """Get current stock status as string"""
        if self.is_low_stock():
            return "Low Stock"
        elif self.is_overstock():
            return "Overstock"
        else:
            return "Normal"
    
    def get_stock_value(self) -> Decimal:
        """Calculate total value of current stock"""
        return self.unit_price * self.current_stock
    
    def can_reduce_stock(self, quantity: int) -> bool:
        """Check if stock can be reduced by given quantity"""
        return self.current_stock >= quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product object to dictionary"""
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_code': self.product_code,
            'category_id': self.category_id,
            'supplier_id': self.supplier_id,
            'unit_price': float(self.unit_price),
            'current_stock': self.current_stock,
            'minimum_stock': self.minimum_stock,
            'maximum_stock': self.maximum_stock,
            'description': self.description,
            'is_active': self.is_active,
            'stock_status': self.get_stock_status(),
            'stock_value': float(self.get_stock_value()),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass 
class StockMovement:
    """Stock movement model for tracking inventory changes"""
    movement_id: Optional[int] = None
    product_id: int = 0
    movement_type: str = ""  
    quantity: int = 0
    unit_price: Optional[Decimal] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    movement_date: Optional[datetime] = None
    created_by: str = "system"
    
    def validate(self) -> bool:
        """Validate stock movement data"""
        valid_types = ['IN', 'OUT', 'ADJUSTMENT']
        if self.movement_type not in valid_types:
            raise ValueError(f"Movement type must be one of: {', '.join(valid_types)}")
        
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        if self.product_id <= 0:
            raise ValueError("Product ID must be valid")
        
        return True
    
    def is_stock_increase(self) -> bool:
        """Check if movement increases stock"""
        return self.movement_type in ['IN', 'ADJUSTMENT'] and self.quantity > 0
    
    def is_stock_decrease(self) -> bool:
        """Check if movement decreases stock"""
        return self.movement_type == 'OUT' or (self.movement_type == 'ADJUSTMENT' and self.quantity < 0)
    
    def get_stock_change(self) -> int:
        """Get the actual stock change (positive or negative)"""
        if self.movement_type == 'IN':
            return self.quantity
        elif self.movement_type == 'OUT':
            return -self.quantity
        else:  # ADJUSTMENT
            return self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stock movement object to dictionary"""
        return {
            'movement_id': self.movement_id,
            'product_id': self.product_id,
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'movement_date': self.movement_date,
            'created_by': self.created_by,
            'stock_change': self.get_stock_change()
        }
