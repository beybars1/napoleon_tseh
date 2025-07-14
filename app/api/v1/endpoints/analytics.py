from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_async_session
from app.models.order import Order, OrderStatus
from app.models.client import Client
from app.models.product import Product
from app.models.conversation import Conversation, ConversationChannel
from app.models.message import Message, MessageDirection
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/sales/overview")
async def get_sales_overview(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get sales overview for the specified period"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Total sales
    total_sales_result = await db.execute(
        select(func.sum(Order.total_amount), func.count(Order.id))
        .where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY])
            )
        )
    )
    total_sales, total_orders = total_sales_result.first()
    
    # Daily sales breakdown
    daily_sales_result = await db.execute(
        select(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('orders')
        )
        .where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY])
            )
        )
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    
    daily_breakdown = []
    for date, revenue, orders in daily_sales_result:
        daily_breakdown.append({
            "date": date.isoformat(),
            "revenue": revenue / 100.0 if revenue else 0.0,
            "orders": orders or 0
        })
    
    # Average order value
    avg_order_value = (total_sales / total_orders) if total_orders > 0 else 0
    
    return {
        "period_days": days,
        "total_revenue": total_sales / 100.0 if total_sales else 0.0,
        "total_orders": total_orders or 0,
        "average_order_value": avg_order_value / 100.0 if avg_order_value else 0.0,
        "daily_breakdown": daily_breakdown
    }


@router.get("/products/performance")
async def get_product_performance(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get product performance analytics"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Top selling products
    from app.models.order import OrderItem
    
    top_products_result = await db.execute(
        select(
            Product.id,
            Product.name,
            Product.category,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.count(OrderItem.id).label('order_count')
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY])
            )
        )
        .group_by(Product.id, Product.name, Product.category)
        .order_by(desc(func.sum(OrderItem.total_price)))
        .limit(limit)
    )
    
    top_products = []
    for product_id, name, category, quantity, revenue, order_count in top_products_result:
        top_products.append({
            "product_id": product_id,
            "name": name,
            "category": category.value,
            "total_quantity": quantity or 0,
            "total_revenue": revenue / 100.0 if revenue else 0.0,
            "order_count": order_count or 0
        })
    
    return {
        "period_days": days,
        "top_products": top_products
    }


@router.get("/customers/insights")
async def get_customer_insights(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get customer insights and analytics"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # New customers
    new_customers_result = await db.execute(
        select(func.count(Client.id))
        .where(
            and_(
                Client.created_at >= start_date,
                Client.created_at <= end_date
            )
        )
    )
    new_customers = new_customers_result.scalar()
    
    # Returning customers (customers who made more than one order)
    returning_customers_result = await db.execute(
        select(func.count(Client.id))
        .where(Client.total_orders > 1)
    )
    returning_customers = returning_customers_result.scalar()
    
    # Top spending customers
    top_customers_result = await db.execute(
        select(
            Client.id,
            Client.first_name,
            Client.last_name,
            Client.phone,
            Client.total_spent,
            Client.total_orders
        )
        .where(Client.total_spent > 0)
        .order_by(desc(Client.total_spent))
        .limit(10)
    )
    
    top_customers = []
    for client_id, first_name, last_name, phone, total_spent, total_orders in top_customers_result:
        full_name = f"{first_name} {last_name}".strip() if first_name or last_name else f"Client {phone}"
        top_customers.append({
            "client_id": client_id,
            "name": full_name,
            "phone": phone,
            "total_spent": total_spent / 100.0,
            "total_orders": total_orders
        })
    
    # Customer acquisition by channel
    channel_result = await db.execute(
        select(
            Conversation.channel,
            func.count(func.distinct(Conversation.client_id)).label('unique_clients')
        )
        .where(
            Conversation.created_at >= start_date
        )
        .group_by(Conversation.channel)
    )
    
    acquisition_channels = {}
    for channel, count in channel_result:
        acquisition_channels[channel.value] = count
    
    return {
        "period_days": days,
        "new_customers": new_customers,
        "returning_customers": returning_customers,
        "top_spending_customers": top_customers,
        "acquisition_channels": acquisition_channels
    }


@router.get("/conversations/analytics")
async def get_conversation_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get conversation and messaging analytics"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Total messages by channel
    channel_messages_result = await db.execute(
        select(
            Conversation.channel,
            func.count(Message.id).label('message_count')
        )
        .join(Message, Conversation.id == Message.conversation_id)
        .where(
            Message.created_at >= start_date
        )
        .group_by(Conversation.channel)
    )
    
    messages_by_channel = {}
    for channel, count in channel_messages_result:
        messages_by_channel[channel.value] = count
    
    # AI response rate
    ai_stats_result = await db.execute(
        select(
            func.count(Message.id).label('total_messages'),
            func.sum(func.case([(Message.ai_processed == True, 1)], else_=0)).label('ai_processed'),
            func.avg(Message.ai_confidence).label('avg_confidence')
        )
        .where(
            and_(
                Message.created_at >= start_date,
                Message.direction == MessageDirection.INCOMING
            )
        )
    )
    
    total_messages, ai_processed, avg_confidence = ai_stats_result.first()
    
    # Response time analysis (simplified)
    response_time_result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', 
                    func.lead(Message.created_at).over(
                        partition_by=Message.conversation_id,
                        order_by=Message.created_at
                    ) - Message.created_at
                )
            ).label('avg_response_time')
        )
        .where(
            and_(
                Message.created_at >= start_date,
                Message.direction == MessageDirection.INCOMING
            )
        )
    )
    
    avg_response_time = response_time_result.scalar()
    
    return {
        "period_days": days,
        "messages_by_channel": messages_by_channel,
        "ai_statistics": {
            "total_incoming_messages": total_messages or 0,
            "ai_processed_messages": ai_processed or 0,
            "ai_processing_rate": (ai_processed / total_messages * 100) if total_messages > 0 else 0,
            "average_confidence": float(avg_confidence) if avg_confidence else 0
        },
        "average_response_time_seconds": float(avg_response_time) if avg_response_time else 0
    }


@router.get("/dashboard/kpis")
async def get_dashboard_kpis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get key performance indicators for dashboard"""
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # Today's metrics
    today_orders_result = await db.execute(
        select(
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('revenue')
        )
        .where(
            and_(
                func.date(Order.created_at) == today,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY])
            )
        )
    )
    today_orders, today_revenue = today_orders_result.first()
    
    # Yesterday's metrics for comparison
    yesterday_orders_result = await db.execute(
        select(
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('revenue')
        )
        .where(
            and_(
                func.date(Order.created_at) == yesterday,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY])
            )
        )
    )
    yesterday_orders, yesterday_revenue = yesterday_orders_result.first()
    
    # This month's metrics
    month_orders_result = await db.execute(
        select(
            func.count(Order.id).label('orders'),
            func.sum(Order.total_amount).label('revenue')
        )
        .where(
            and_(
                Order.created_at >= this_month,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.READY])
            )
        )
    )
    month_orders, month_revenue = month_orders_result.first()
    
    # Active conversations
    active_conversations_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.status == "active")
    )
    active_conversations = active_conversations_result.scalar()
    
    # Pending orders
    pending_orders_result = await db.execute(
        select(func.count(Order.id))
        .where(Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED]))
    )
    pending_orders = pending_orders_result.scalar()
    
    return {
        "today": {
            "orders": today_orders or 0,
            "revenue": today_revenue / 100.0 if today_revenue else 0.0,
            "orders_change": ((today_orders or 0) - (yesterday_orders or 0)),
            "revenue_change": ((today_revenue or 0) - (yesterday_revenue or 0)) / 100.0
        },
        "this_month": {
            "orders": month_orders or 0,
            "revenue": month_revenue / 100.0 if month_revenue else 0.0
        },
        "operational": {
            "active_conversations": active_conversations or 0,
            "pending_orders": pending_orders or 0
        }
    } 