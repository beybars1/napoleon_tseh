from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime, timedelta

from app.core.database import get_async_session
from app.models.order import Order, OrderStatus, OrderItem
from app.models.client import Client
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.message import Message, MessageDirection

router = APIRouter()

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()


@router.get("/overview")
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_async_session)
):
    """Get dashboard overview statistics"""
    
    try:
        # Get today's date range
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Total orders today
        result = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.created_at >= today,
                    Order.created_at < tomorrow
                )
            )
        )
        orders_today = result.scalar()
        
        # Pending orders
        result = await db.execute(
            select(func.count(Order.id)).where(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED])
            )
        )
        pending_orders = result.scalar()
        
        # Orders in preparation
        result = await db.execute(
            select(func.count(Order.id)).where(
                Order.status == OrderStatus.PREPARING
            )
        )
        preparing_orders = result.scalar()
        
        # Ready orders
        result = await db.execute(
            select(func.count(Order.id)).where(
                Order.status == OrderStatus.READY
            )
        )
        ready_orders = result.scalar()
        
        # Active conversations
        result = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.status == "active"
            )
        )
        active_conversations = result.scalar()
        
        # Revenue today
        result = await db.execute(
            select(func.sum(Order.total_amount)).where(
                and_(
                    Order.created_at >= today,
                    Order.created_at < tomorrow,
                    Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY])
                )
            )
        )
        revenue_today = result.scalar() or 0
        
        return {
            "orders_today": orders_today,
            "pending_orders": pending_orders,
            "preparing_orders": preparing_orders,
            "ready_orders": ready_orders,
            "active_conversations": active_conversations,
            "revenue_today": revenue_today / 100.0  # Convert cents to dollars
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/active")
async def get_active_orders(
    db: AsyncSession = Depends(get_async_session)
):
    """Get all active orders for the kitchen dashboard"""
    
    try:
        # Get orders that need attention (not delivered or cancelled)
        result = await db.execute(
            select(Order)
            .where(
                Order.status.in_([
                    OrderStatus.PENDING,
                    OrderStatus.CONFIRMED,
                    OrderStatus.PREPARING,
                    OrderStatus.READY,
                    OrderStatus.OUT_FOR_DELIVERY
                ])
            )
            .order_by(Order.created_at.asc())
        )
        orders = result.scalars().all()
        
        # Format orders with client and items information
        formatted_orders = []
        for order in orders:
            # Get client
            client_result = await db.execute(
                select(Client).where(Client.id == order.client_id)
            )
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
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "size": item.size,
                    "flavor": item.flavor,
                    "decorations": item.decorations,
                    "customizations": item.customizations,
                    "special_instructions": item.special_instructions,
                    "unit_price": item.unit_price / 100.0,
                    "total_price": item.total_price / 100.0
                })
            
            formatted_orders.append({
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status.value,
                "delivery_method": order.delivery_method.value,
                "client": {
                    "id": client.id,
                    "name": client.full_name,
                    "phone": client.phone
                },
                "items": items,
                "total_amount": order.total_amount / 100.0,
                "special_instructions": order.special_instructions,
                "requested_delivery_time": order.requested_delivery_time.isoformat() if order.requested_delivery_time else None,
                "estimated_completion_time": order.estimated_completion_time.isoformat() if order.estimated_completion_time else None,
                "created_at": order.created_at.isoformat(),
                "time_elapsed": str(datetime.now() - order.created_at)
            })
        
        return formatted_orders
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    db: AsyncSession = Depends(get_async_session)
):
    """Update order status"""
    
    try:
        # Get order
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update status
        old_status = order.status
        order.status = new_status
        
        # Update completion time if order is ready
        if new_status == OrderStatus.READY:
            order.actual_completion_time = datetime.now()
        
        await db.commit()
        
        # Broadcast update to connected clients
        await manager.broadcast(json.dumps({
            "type": "order_status_update",
            "order_id": order_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "timestamp": datetime.now().isoformat()
        }))
        
        return {"message": "Order status updated successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get detailed order information"""
    
    try:
        # Get order
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get client
        client_result = await db.execute(
            select(Client).where(Client.id == order.client_id)
        )
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
                    "category": product.category.value,
                    "preparation_time": product.preparation_time
                },
                "quantity": item.quantity,
                "size": item.size,
                "flavor": item.flavor,
                "decorations": item.decorations,
                "customizations": item.customizations,
                "special_instructions": item.special_instructions,
                "unit_price": item.unit_price / 100.0,
                "total_price": item.total_price / 100.0
            })
        
        # Get recent conversations with client
        conversations_result = await db.execute(
            select(Conversation)
            .where(Conversation.client_id == client.id)
            .order_by(desc(Conversation.last_message_at))
            .limit(3)
        )
        conversations = conversations_result.scalars().all()
        
        recent_messages = []
        for conversation in conversations:
            messages_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(desc(Message.created_at))
                .limit(5)
            )
            messages = messages_result.scalars().all()
            
            for message in messages:
                recent_messages.append({
                    "id": message.id,
                    "channel": conversation.channel.value,
                    "direction": message.direction.value,
                    "content": message.content,
                    "created_at": message.created_at.isoformat()
                })
        
        return {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "delivery_method": order.delivery_method.value,
            "client": {
                "id": client.id,
                "name": client.full_name,
                "phone": client.phone,
                "email": client.email,
                "total_orders": client.total_orders,
                "total_spent": client.total_spent / 100.0
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
                "actual_completion_time": order.actual_completion_time.isoformat() if order.actual_completion_time else None,
                "created_at": order.created_at.isoformat()
            },
            "special_instructions": order.special_instructions,
            "notes": order.notes,
            "recent_messages": recent_messages[:10]  # Last 10 messages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates"""
    
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Handle different message types
            message_data = json.loads(data)
            
            if message_data.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message_data.get("type") == "subscribe":
                # Client wants to subscribe to specific updates
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "message": "Connected to dashboard updates"
                }))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/queue/summary")
async def get_queue_summary(
    db: AsyncSession = Depends(get_async_session)
):
    """Get queue summary for kitchen display"""
    
    try:
        # Get orders by status
        result = await db.execute(
            select(Order.status, func.count(Order.id))
            .where(
                Order.status.in_([
                    OrderStatus.PENDING,
                    OrderStatus.CONFIRMED,
                    OrderStatus.PREPARING,
                    OrderStatus.READY
                ])
            )
            .group_by(Order.status)
        )
        
        status_counts = dict(result.all())
        
        # Get average preparation time
        result = await db.execute(
            select(func.avg(
                func.extract('epoch', Order.actual_completion_time - Order.created_at)
            ))
            .where(
                and_(
                    Order.actual_completion_time.isnot(None),
                    Order.created_at >= datetime.now() - timedelta(days=7)
                )
            )
        )
        avg_prep_time = result.scalar() or 0
        
        # Get next orders to prepare
        result = await db.execute(
            select(Order, Client)
            .join(Client, Order.client_id == Client.id)
            .where(Order.status == OrderStatus.CONFIRMED)
            .order_by(Order.created_at.asc())
            .limit(5)
        )
        
        next_orders = []
        for order, client in result.all():
            next_orders.append({
                "id": order.id,
                "order_number": order.order_number,
                "client_name": client.full_name,
                "created_at": order.created_at.isoformat(),
                "requested_time": order.requested_delivery_time.isoformat() if order.requested_delivery_time else None
            })
        
        return {
            "queue_counts": {
                "pending": status_counts.get(OrderStatus.PENDING, 0),
                "confirmed": status_counts.get(OrderStatus.CONFIRMED, 0),
                "preparing": status_counts.get(OrderStatus.PREPARING, 0),
                "ready": status_counts.get(OrderStatus.READY, 0)
            },
            "average_prep_time_minutes": int(avg_prep_time / 60) if avg_prep_time else 0,
            "next_orders": next_orders
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 