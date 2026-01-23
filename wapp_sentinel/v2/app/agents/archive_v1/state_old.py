"""State definition for LangGraph order collection workflow"""
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime


class OrderState(TypedDict):
    """
    State for the order collection conversation.
    This state is passed between all nodes in the LangGraph workflow.
    """
    # Conversation context
    chat_id: str
    conversation_id: int
    messages: List[Dict[str, str]]  # [{"role": "user/assistant", "content": "..."}]
    
    # Order data being collected
    items: Optional[List[Dict[str, Any]]]  # [{"name": "...", "quantity": "...", "notes": "..."}]
    delivery_datetime: Optional[str]  # ISO format datetime string
    delivery_address: Optional[str]
    payment_status: Optional[str]  # "paid", "unpaid", "unknown"
    client_name: Optional[str]
    client_phone: Optional[str]
    additional_phone: Optional[str]
    notes: Optional[str]
    
    # Progress tracking flags
    has_items: bool
    has_delivery_info: bool
    has_payment_info: bool
    has_contact_info: bool
    order_validated: bool
    order_confirmed: bool
    
    # Workflow control
    current_step: str  # Which node we're currently at
    needs_clarification: bool
    clarification_topic: Optional[str]  # What needs to be clarified
    retry_count: int  # Number of retries for current step
    
    # Meta information
    started_at: str  # ISO format datetime
    last_user_message: str
    last_assistant_message: str
    
    def __init__(self):
        """Initialize with default values"""
        self.messages = []
        self.items = None
        self.delivery_datetime = None
        self.delivery_address = None
        self.payment_status = None
        self.client_name = None
        self.client_phone = None
        self.additional_phone = None
        self.notes = None
        self.has_items = False
        self.has_delivery_info = False
        self.has_payment_info = False
        self.has_contact_info = False
        self.order_validated = False
        self.order_confirmed = False
        self.current_step = "greet"
        self.needs_clarification = False
        self.clarification_topic = None
        self.retry_count = 0
        self.started_at = datetime.now().isoformat()
        self.last_user_message = ""
        self.last_assistant_message = ""
