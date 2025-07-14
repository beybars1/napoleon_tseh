from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_async_session
from app.models.order import Order, OrderStatus, OrderItem, PaymentStatus, DeliveryMethod
from app.models.client import Client
from app.models.product import Product
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[OrderStatus] = Query(None),
    client_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all orders with filtering"""
    
    query = select(Order, Client).join(Client, Order.client_id == Client.id)
    
    if status:
        query = query.where(Order.status == status)
    
    if client_id:
        query = query.where(Order.client_id == client_id)
    
    query = query.order_by(desc(Order.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    orders_data = result.all()
    
    formatted_orders = []
    for order, client in orders_data:
        formatted_orders.append({
            "id": order.id,
            "uuid": order.uuid,
            "order_number": order.order_number,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "delivery_method": order.delivery_method.value,
            "client": {
                "id": client.id,
                "name": client.full_name,
                "phone": client.phone
            },
            "total_amount": order.total_amount / 100.0,
            "created_at": order.created_at.isoformat(),
            "requested_delivery_time": order.requested_delivery_time.isoformat() if order.requested_delivery_time else None
        })
    
    return formatted_orders


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific order details"""
    
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get client
    client_result = await db.execute(select(Client).where(Client.id == order.client_id))
    client = client_result.scalar_one()
    
    # Get order items
    items_result = await db.execute(
        select(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .where(OrderItem.order_id == order.id)
    )
    items_data = items_result.all()
    
    items = []
    for item, product in items_data:
        items.append({
            "id": item.id,
            "product": {
                "id": product.id,
                "name": product.name,
                "category": product.category.value
            },
            "quantity": item.quantity,
            "unit_price": item.unit_price / 100.0,
            "total_price": item.total_price / 100.0,
            "size": item.size,
            "flavor": item.flavor,
            "decorations": item.decorations,
            "customizations": item.customizations,
            "special_instructions": item.special_instructions
        })
    
    return {
        "id": order.id,
        "uuid": order.uuid,
        "order_number": order.order_number,
        "status": order.status.value,
        "payment_status": order.payment_status.value,
        "delivery_method": order.delivery_method.value,
        "client": {
            "id": client.id,
            "name": client.full_name,
            "phone": client.phone,
            "email": client.email
        },
        "items": items,
        "pricing": {
            "subtotal": order.subtotal / 100.0,
            "tax_amount": order.tax_amount / 100.0,
            "delivery_fee": order.delivery_fee / 100.0,
            "discount_amount": order.discount_amount / 100.0,
            "total_amount": order.total_amount / 100.0
        },
        "delivery": {
            "address": order.delivery_address,
            "city": order.delivery_city,
            "postal_code": order.delivery_postal_code,
            "instructions": order.delivery_instructions
        },
        "timing": {
            "requested_delivery_time": order.requested_delivery_time.isoformat() if order.requested_delivery_time else None,
            "estimated_completion_time": order.estimated_completion_time.isoformat() if order.estimated_completion_time else None,
            "actual_completion_time": order.actual_completion_time.isoformat() if order.actual_completion_time else None
        },
        "special_instructions": order.special_instructions,
        "notes": order.notes,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat() if order.updated_at else None
    }


@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: OrderStatus,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update order status"""
    
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status
    
    # Update completion time if order is ready
    if status == OrderStatus.READY:
        order.actual_completion_time = datetime.now()
    
    await db.commit()
    
    return {"message": "Order status updated successfully"}


@router.put("/{order_id}/payment-status")
async def update_payment_status(
    order_id: int,
    payment_status: PaymentStatus,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update payment status"""
    
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.payment_status = payment_status
    await db.commit()
    
    return {"message": "Payment status updated successfully"}


@router.post("/")
async def create_order(
    client_id: int,
    items: List[dict],
    delivery_method: DeliveryMethod = DeliveryMethod.PICKUP,
    delivery_address: Optional[str] = None,
    special_instructions: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new order"""
    
    # Verify client exists
    client_result = await db.execute(select(Client).where(Client.id == client_id))
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Generate order number
    order_count = await db.execute(select(func.count(Order.id)))
    order_number = f"ORD{order_count.scalar() + 1:06d}"
    
    # Create order
    order = Order(
        client_id=client_id,
        order_number=order_number,
        delivery_method=delivery_method,
        delivery_address=delivery_address,
        special_instructions=special_instructions,
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING
    )
    
    db.add(order)
    await db.flush()  # Get the order ID
    
    # Add order items
    subtotal = 0
    for item_data in items:
        # Get product
        product_result = await db.execute(
            select(Product).where(Product.id == item_data["product_id"])
        )
        product = product_result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data['product_id']} not found")
        
        quantity = item_data["quantity"]
        unit_price = product.price
        total_price = unit_price * quantity
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            size=item_data.get("size"),
            flavor=item_data.get("flavor"),
            decorations=item_data.get("decorations"),
            customizations=item_data.get("customizations"),
            special_instructions=item_data.get("special_instructions")
        )
        
        db.add(order_item)
        subtotal += total_price
    
    # Calculate totals
    order.subtotal = subtotal
    order.tax_amount = int(subtotal * 0.1)  # 10% tax
    order.delivery_fee = 500 if delivery_method == DeliveryMethod.DELIVERY else 0  # $5 delivery fee
    order.total_amount = order.subtotal + order.tax_amount + order.delivery_fee
    
    # Update client statistics
    client.total_orders += 1
    client.total_spent += order.total_amount
    client.last_order = datetime.now()
    
    await db.commit()
    await db.refresh(order)
    
    return {
        "message": "Order created successfully",
        "order": {
            "id": order.id,
            "order_number": order.order_number,
            "total_amount": order.total_amount / 100.0
        }
    }


@router.get("/stats/summary")
async def get_order_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get order statistics summary"""
    
    # Total orders
    total_result = await db.execute(select(func.count(Order.id)))
    total_orders = total_result.scalar()
    
    # Orders by status
    status_result = await db.execute(
        select(Order.status, func.count(Order.id))
        .group_by(Order.status)
    )
    status_counts = dict(status_result.all())
    
    # Total revenue
    revenue_result = await db.execute(
        select(func.sum(Order.total_amount))
        .where(Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY]))
    )
    total_revenue = revenue_result.scalar() or 0
    
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue / 100.0,
        "status_breakdown": {
            status.value: status_counts.get(status, 0)
            for status in OrderStatus
        }
    }