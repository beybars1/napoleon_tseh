from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_async_session
from app.models.client import Client
from app.models.order import Order
from app.models.conversation import Conversation
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all clients with pagination and search"""
    
    query = select(Client)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Client.first_name.ilike(search_term)) |
            (Client.last_name.ilike(search_term)) |
            (Client.phone.ilike(search_term)) |
            (Client.email.ilike(search_term))
        )
    
    query = query.order_by(desc(Client.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    clients = result.scalars().all()
    
    # Format response
    formatted_clients = []
    for client in clients:
        formatted_clients.append({
            "id": client.id,
            "uuid": client.uuid,
            "full_name": client.full_name,
            "phone": client.phone,
            "email": client.email,
            "whatsapp_id": client.whatsapp_id,
            "telegram_id": client.telegram_id,
            "instagram_handle": client.instagram_handle,
            "total_orders": client.total_orders,
            "total_spent": client.total_spent / 100.0,
            "is_active": client.is_active,
            "created_at": client.created_at.isoformat(),
            "last_contact": client.last_contact.isoformat() if client.last_contact else None,
            "last_order": client.last_order.isoformat() if client.last_order else None
        })
    
    return formatted_clients


@router.get("/{client_id}")
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific client details"""
    
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get recent orders
    orders_result = await db.execute(
        select(Order)
        .where(Order.client_id == client_id)
        .order_by(desc(Order.created_at))
        .limit(10)
    )
    recent_orders = orders_result.scalars().all()
    
    # Get active conversations
    conversations_result = await db.execute(
        select(Conversation)
        .where(Conversation.client_id == client_id)
        .order_by(desc(Conversation.last_message_at))
        .limit(5)
    )
    conversations = conversations_result.scalars().all()
    
    return {
        "id": client.id,
        "uuid": client.uuid,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "full_name": client.full_name,
        "phone": client.phone,
        "email": client.email,
        "whatsapp_id": client.whatsapp_id,
        "telegram_id": client.telegram_id,
        "instagram_handle": client.instagram_handle,
        "address": client.address,
        "city": client.city,
        "postal_code": client.postal_code,
        "preferences": client.preferences,
        "tags": client.tags,
        "notes": client.notes,
        "total_orders": client.total_orders,
        "total_spent": client.total_spent / 100.0,
        "is_active": client.is_active,
        "is_blocked": client.is_blocked,
        "created_at": client.created_at.isoformat(),
        "last_contact": client.last_contact.isoformat() if client.last_contact else None,
        "last_order": client.last_order.isoformat() if client.last_order else None,
        "recent_orders": [
            {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status.value,
                "total_amount": order.total_amount / 100.0,
                "created_at": order.created_at.isoformat()
            }
            for order in recent_orders
        ],
        "conversations": [
            {
                "id": conv.id,
                "channel": conv.channel.value,
                "status": conv.status.value,
                "message_count": conv.message_count,
                "unread_count": conv.unread_count,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None
            }
            for conv in conversations
        ]
    }


@router.put("/{client_id}")
async def update_client(
    client_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    postal_code: Optional[str] = None,
    preferences: Optional[dict] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update client information"""
    
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Update fields
    if first_name is not None:
        client.first_name = first_name
    if last_name is not None:
        client.last_name = last_name
    if email is not None:
        client.email = email
    if address is not None:
        client.address = address
    if city is not None:
        client.city = city
    if postal_code is not None:
        client.postal_code = postal_code
    if preferences is not None:
        client.preferences = preferences
    if tags is not None:
        client.tags = tags
    if notes is not None:
        client.notes = notes
    
    await db.commit()
    
    return {"message": "Client updated successfully"}


@router.get("/stats/summary")
async def get_client_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get client statistics summary"""
    
    # Total clients
    total_clients_result = await db.execute(select(func.count(Client.id)))
    total_clients = total_clients_result.scalar()
    
    # Active clients (had contact in last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_clients_result = await db.execute(
        select(func.count(Client.id)).where(
            Client.last_contact >= thirty_days_ago
        )
    )
    active_clients = active_clients_result.scalar()
    
    # New clients this month
    this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_clients_result = await db.execute(
        select(func.count(Client.id)).where(
            Client.created_at >= this_month
        )
    )
    new_clients = new_clients_result.scalar()
    
    # Top spending clients
    top_clients_result = await db.execute(
        select(Client)
        .where(Client.total_spent > 0)
        .order_by(desc(Client.total_spent))
        .limit(10)
    )
    top_clients = top_clients_result.scalars().all()
    
    return {
        "total_clients": total_clients,
        "active_clients": active_clients,
        "new_clients_this_month": new_clients,
        "top_spending_clients": [
            {
                "id": client.id,
                "name": client.full_name,
                "phone": client.phone,
                "total_spent": client.total_spent / 100.0,
                "total_orders": client.total_orders
            }
            for client in top_clients
        ]
    } 