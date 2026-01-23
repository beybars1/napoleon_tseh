"""
ConversationState - Enhanced state schema for v2 intent-driven architecture
"""
from typing import TypedDict, Literal, Optional
from datetime import datetime


class OrderDraft(TypedDict, total=False):
    """Order draft being constructed during conversation"""
    items: list[dict]  # [{"product_id": str, "quantity": float, "price": float}]
    pickup_date: Optional[str]
    pickup_time: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    payment_method: Optional[str]
    special_requests: Optional[str]
    total_amount: Optional[float]
    completeness: dict[str, bool]  # {"items": bool, "pickup": bool, "customer": bool, "payment": bool}


class ConversationState(TypedDict):
    """State for conversation processing"""
    # Core identifiers
    conversation_id: int
    chat_id: str
    
    # Message history
    messages: list[dict]  # [{"role": "user"/"assistant", "content": str, "timestamp": datetime}]
    
    # Order draft
    order_draft: OrderDraft
    
    # Intent tracking
    last_intent: Optional[str]  # Last classified intent
    conversation_stage: Literal["greeting", "inquiry", "ordering", "confirming", "reset_confirmation", "post_order", "completed", "escalated"]
    
    # Escalation tracking
    clarification_count: int  # Number of clarification attempts
    flagged_for_human: bool
    escalation_reason: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Next action
    next_step: str  # Node to execute next
