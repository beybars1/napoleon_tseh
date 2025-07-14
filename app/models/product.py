from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid

from app.core.database import Base


class ProductCategory(enum.Enum):
    CAKE = "cake"
    CUPCAKE = "cupcake"
    PASTRY = "pastry"
    COOKIE = "cookie"
    BREAD = "bread"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    OTHER = "other"


class ProductStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    SEASONAL = "seasonal"


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(Enum(ProductCategory), nullable=False)
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    
    # Pricing (stored in cents)
    price = Column(Integer, nullable=False)  # Base price in cents
    cost = Column(Integer, nullable=True)  # Cost to make in cents
    
    # Product details
    ingredients = Column(JSON, nullable=True)  # List of ingredients
    allergens = Column(JSON, nullable=True)  # List of allergens
    nutritional_info = Column(JSON, nullable=True)  # Nutritional information
    
    # Customization options
    sizes = Column(JSON, nullable=True)  # Available sizes with price modifiers
    flavors = Column(JSON, nullable=True)  # Available flavors
    decorations = Column(JSON, nullable=True)  # Available decorations with prices
    
    # Inventory and preparation
    preparation_time = Column(Integer, nullable=True)  # Time in minutes
    advance_notice = Column(Integer, nullable=True)  # Required advance notice in hours
    stock_quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=0)
    
    # Media and display
    image_url = Column(String, nullable=True)
    images = Column(JSON, nullable=True)  # Multiple images
    display_order = Column(Integer, default=0)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Tags for search and filtering
    is_featured = Column(Boolean, default=False)
    is_available_online = Column(Boolean, default=True)
    is_customizable = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    
    @property
    def price_display(self):
        """Get price in dollars"""
        return self.price / 100.0
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0 or self.stock_quantity == -1  # -1 means unlimited
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, category={self.category})>" 