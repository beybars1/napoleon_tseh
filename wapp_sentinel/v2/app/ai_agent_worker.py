"""
AI Agent Worker - Consumes ai_agent_interactions queue and manages conversations using LangGraph
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pika
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database.models import Conversation, ConversationMessage, AIGeneratedOrder
from app.agents.order_graph import order_graph
from app.agents.state import ConversationState
import httpx
import asyncio
from sqlalchemy import and_

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
AI_AGENT_QUEUE = os.getenv("AI_AGENT_QUEUE", "ai_agent_queue")

# Green API credentials
GREENAPI_BASE_URL = os.getenv("GREENAPI_BASE_URL", "https://api.green-api.com")
GREENAPI_INSTANCE = os.getenv("GREENAPI_INSTANCE")
GREENAPI_TOKEN = os.getenv("GREENAPI_TOKEN")


def extract_source_message_id(body: dict) -> str | None:
    raw_data = body.get("raw_data") or {}
    source_message_id = body.get("message_id")
    if not source_message_id:
        source_message_id = raw_data.get("idMessage") or raw_data.get("receiptId")
    return str(source_message_id) if source_message_id else None


def is_duplicate_message(db: Session, conversation_id: int, source_message_id: str | None) -> bool:
    if not source_message_id:
        return False
    existing = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id,
        ConversationMessage.message_metadata["source_message_id"].astext == source_message_id
    ).first()
    return existing is not None


def get_or_create_conversation(db: Session, chat_id: str, sender_name: str = None, sender_phone: str = None) -> Conversation:
    """
    Get active conversation for chat_id or create new one.
    If existing conversation is escalated, create new one.
    If recently completed (< 24 hours), reopen for edits.
    """
    # Check for active conversation
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == chat_id,
        Conversation.status == "active",
        Conversation.flagged_for_human == False
    ).first()

    if conversation:
        return conversation

    # Check for recently completed conversation (within last 24 hours)
    from datetime import timedelta, timezone
    now_utc = datetime.now(timezone.utc)
    recent_completed = db.query(Conversation).filter(
        Conversation.chat_id == chat_id,
        Conversation.status == "completed",
        Conversation.completed_at >= now_utc - timedelta(hours=24)
    ).order_by(Conversation.completed_at.desc()).first()

    if recent_completed:
        # Reopen conversation - let router decide what to do based on intent
        # Don't force "confirming" stage - set to "post_order" to indicate there's a recent order
        recent_completed.status = "active"
        recent_completed.conversation_stage = "post_order"  # Special stage: has confirmed order
        recent_completed.updated_at = datetime.now()
        db.commit()
        logger.info(f"Reopened conversation {recent_completed.id} (post_order stage, was completed at {recent_completed.completed_at})")
        return recent_completed

    # Create new conversation
    conversation = Conversation(
        chat_id=chat_id,
        sender_name=sender_name,
        sender_phone=sender_phone,
        status="active",
        current_step="greet",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    logger.info(f"Created new conversation {conversation.id} for chat {chat_id}")

    return conversation


def load_conversation_state(db: Session, conversation: Conversation) -> ConversationState:
    """
    Load conversation history into ConversationState (v2).
    """
    # Get all messages for this conversation
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation.id
    ).order_by(ConversationMessage.timestamp.asc()).all()
    
    # Load existing order draft from AIGeneratedOrder if exists
    order_draft = {
        "items": [],
        "completeness": {"items": False, "pickup": False, "customer": False, "payment": False}
    }

    # Load order if it's pending (draft) OR if conversation is being reopened for editing
    ai_order = db.query(AIGeneratedOrder).filter(
        AIGeneratedOrder.conversation_id == conversation.id,
        AIGeneratedOrder.validation_status.in_(['pending', 'pending_validation', 'validated'])
    ).order_by(AIGeneratedOrder.created_at.desc()).first()

    logger.info(f"[LOAD] Conversation stage: {conversation.conversation_stage}, Found ai_order: {ai_order.id if ai_order else 'None'}, status: {ai_order.validation_status if ai_order else 'None'}, items: {ai_order.items if ai_order else 'None'}")

    if ai_order:
        # Restore order draft from database
        order_draft["items"] = ai_order.items or []
        logger.info(f"[LOAD] Loaded {len(order_draft['items'])} items from DB")
        order_draft["pickup_date"] = None
        order_draft["pickup_time"] = None
        if ai_order.estimated_delivery_datetime:
            order_draft["pickup_date"] = ai_order.estimated_delivery_datetime.strftime("%d.%m.%Y")
            order_draft["pickup_time"] = ai_order.estimated_delivery_datetime.strftime("%H:%M")
        order_draft["customer_name"] = ai_order.client_name
        order_draft["customer_phone"] = ai_order.client_phone
        order_draft["payment_method"] = ai_order.payment_status
        order_draft["special_requests"] = ai_order.notes
        
        # Recalculate total (price is already total: price_per_kg * quantity)
        total = sum(item.get("price", 0) for item in order_draft["items"])
        order_draft["total_amount"] = total
        
        # Recalculate completeness
        from app.agents.tools.order_tools import check_order_completeness
        order_draft["completeness"] = check_order_completeness(order_draft)
    
    # Initialize state
    state = ConversationState(
        conversation_id=conversation.id,
        chat_id=conversation.chat_id,
        messages=[
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ],
        order_draft=order_draft,
        last_intent=conversation.last_intent,
        conversation_stage=conversation.conversation_stage or "greeting",
        clarification_count=conversation.clarification_count or 0,
        flagged_for_human=conversation.flagged_for_human or False,
        escalation_reason=conversation.escalation_reason,
        created_at=conversation.created_at,
        updated_at=datetime.now(),
        next_step="router"
    )
    
    return state


def save_conversation_state(db: Session, conversation: Conversation, state: ConversationState):
    """
    Save conversation state to database (v2).
    """
    # Update conversation with v2 fields
    conversation.last_intent = state.get("last_intent")
    conversation.conversation_stage = state.get("conversation_stage")
    conversation.clarification_count = state.get("clarification_count", 0)
    conversation.flagged_for_human = state.get("flagged_for_human", False)
    conversation.escalation_reason = state.get("escalation_reason")
    conversation.updated_at = datetime.now()
    
    # Save new messages
    existing_count = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation.id
    ).count()
    
    new_messages = state["messages"][existing_count:]
    for msg in new_messages:
        conv_msg = ConversationMessage(
            conversation_id=conversation.id,
            role=msg["role"],
            content=msg["content"],
            intent=state.get("last_intent") if msg["role"] == "user" else None,
            timestamp=msg.get("timestamp", datetime.now()),
            message_metadata=msg.get("metadata")
        )
        db.add(conv_msg)
    
    # Save or update AI order if order_draft has items
    order_draft = state.get("order_draft", {})
    logger.info(f"[SAVE] order_draft items: {order_draft.get('items')}, customer: {order_draft.get('customer_name')}")
    if order_draft.get("items"):
        # Match the load query - look for pending, pending_validation, or validated orders
        ai_order = db.query(AIGeneratedOrder).filter(
            AIGeneratedOrder.conversation_id == conversation.id,
            AIGeneratedOrder.validation_status.in_(['pending', 'pending_validation', 'validated'])
        ).first()

        logger.info(f"[SAVE] Found existing ai_order: {ai_order.id if ai_order else 'None'}, status: {ai_order.validation_status if ai_order else 'None'}")

        if not ai_order:
            ai_order = AIGeneratedOrder(
                conversation_id=conversation.id,
                chat_id=conversation.chat_id,
                validation_status="pending"
            )
            db.add(ai_order)
            logger.info(f"[SAVE] Created new AIGeneratedOrder")
        else:
            # If we're editing a validated/pending_validation order, revert to pending
            if ai_order.validation_status in ['pending_validation', 'validated'] and state.get('conversation_stage') != 'completed':
                ai_order.validation_status = 'pending'
                logger.info(f"[SAVE] Reverted order {ai_order.id} status to 'pending' for editing")

        # Update order data from order_draft
        ai_order.items = order_draft.get("items")
        ai_order.client_name = order_draft.get("customer_name")
        ai_order.client_phone = order_draft.get("customer_phone")
        ai_order.payment_status = order_draft.get("payment_method")
        ai_order.notes = order_draft.get("special_requests")
        logger.info(f"[SAVE] Updated ai_order with {len(order_draft.get('items', []))} items")
        
        # Parse pickup date/time if available
        if order_draft.get("pickup_date") and order_draft.get("pickup_time"):
            try:
                from datetime import datetime as dt
                date_str = order_draft["pickup_date"]
                time_str = order_draft["pickup_time"]
                # Parse date (DD.MM.YYYY or similar)
                for fmt in ["%d.%m.%Y", "%d.%m.%y"]:
                    try:
                        pickup_dt = dt.strptime(f"{date_str} {time_str}", f"{fmt} %H:%M")
                        ai_order.estimated_delivery_datetime = pickup_dt
                        break
                    except:
                        continue
            except:
                pass
        
        # If order confirmed and complete
        completeness = order_draft.get("completeness", {})
        if all(completeness.values()) and state.get("conversation_stage") == "completed":
            ai_order.validation_status = "validated"
            ai_order.confirmed_at = datetime.now()
            conversation.status = "completed"
            conversation.completed_at = datetime.now()
    
    db.commit()
    logger.info(f"Saved state for conversation {conversation.id}")


async def send_whatsapp_message(chat_id: str, message: str):
    """
    Send message via Green API.
    """
    if not GREENAPI_INSTANCE or not GREENAPI_TOKEN:
        logger.error("GREENAPI_INSTANCE or GREENAPI_TOKEN not configured")
        return
    
    url = f"{GREENAPI_BASE_URL}/waInstance{GREENAPI_INSTANCE}/sendMessage/{GREENAPI_TOKEN}"
    
    payload = {
        "chatId": chat_id,
        "message": message
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Sent message to {chat_id}: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")


def process_message(body: dict):
    """
    Process incoming message through LangGraph workflow.
    """
    logger.info(f"Processing message: {body}")
    
    chat_id = body.get("chat_id")
    message_text = body.get("text", "")
    sender_name = body.get("sender_name")
    raw_data = body.get("raw_data") or {}
    source_message_id = extract_source_message_id(body)
    
    if not chat_id:
        logger.error("No chat_id in message")
        return
    
    db = SessionLocal()
    try:
        # Get or create conversation
        conversation = get_or_create_conversation(db, chat_id, sender_name)
        
        # Load state
        state = load_conversation_state(db, conversation)

        if is_duplicate_message(db, conversation.id, source_message_id):
            logger.info(
                "Duplicate message_id detected; skipping processing. chat_id=%s source_message_id=%s",
                chat_id,
                source_message_id
            )
            return

        last_user_msg = next((m for m in reversed(state["messages"]) if m["role"] == "user"), None)
        if last_user_msg:
            last_content = (last_user_msg.get("content") or "").strip()
            incoming_content = (message_text or "").strip()
            if last_content and last_content == incoming_content:
                last_ts = last_user_msg.get("timestamp")
                if isinstance(last_ts, datetime):
                    now = datetime.now(last_ts.tzinfo) if last_ts.tzinfo else datetime.now()
                    if abs((now - last_ts).total_seconds()) <= 10:
                        logger.info("Duplicate user message detected; skipping processing.")
                        return
        
        # Count messages BEFORE adding new user message
        messages_before = len(state["messages"])
        
        # Add user message to state
        state["messages"].append({
            "role": "user",
            "content": message_text,
            "timestamp": datetime.now(),
            "metadata": {
                "source_message_id": source_message_id,
                "raw_data": raw_data
            }
        })
        
        # Run graph
        result = order_graph.invoke(state)
        
        # Save updated state
        save_conversation_state(db, conversation, result)
        
        # Send all new assistant messages to WhatsApp
        # Count from messages_before + 1 (after user message)
        new_messages = result["messages"][messages_before + 1:]
        
        for msg in new_messages:
            if msg["role"] == "assistant":
                asyncio.run(send_whatsapp_message(chat_id, msg["content"]))
        
        logger.info(f"Processed message for conversation {conversation.id}, stage: {result.get('conversation_stage')}, sent {len([m for m in new_messages if m['role']=='assistant'])} messages")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def callback(ch, method, properties, body):
    """
    RabbitMQ callback for processing messages.
    """
    try:
        message = json.loads(body)
        process_message(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error in callback: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """
    Main worker loop.
    """
    logger.info("Starting AI Agent Worker...")
    logger.info(f"Connecting to RabbitMQ at {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    
    # Setup RabbitMQ connection with credentials
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    # Declare queue
    channel.queue_declare(queue=AI_AGENT_QUEUE, durable=True)
    
    # Set QoS
    channel.basic_qos(prefetch_count=1)
    
    # Start consuming
    channel.basic_consume(
        queue=AI_AGENT_QUEUE,
        on_message_callback=callback
    )
    
    logger.info(f"Waiting for messages in queue: {AI_AGENT_QUEUE}")
    logger.info("Press CTRL+C to exit")
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping worker...")
        channel.stop_consuming()
    finally:
        connection.close()
        logger.info("Connection closed")


if __name__ == "__main__":
    main()
