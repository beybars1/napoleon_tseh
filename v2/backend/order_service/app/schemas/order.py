from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.order import OrderStatus

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    total_price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    customer_id: int
    status: OrderStatus
    total_amount: float
    delivery_address: Optional[str] = None
    delivery_date: Optional[datetime] = None
    special_instructions: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[OrderItem]

    class Config:
        from_attributes = True
