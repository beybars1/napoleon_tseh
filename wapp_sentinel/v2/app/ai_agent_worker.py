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
from app.agents.state import OrderState
import httpx
import asyncio

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
QUEUE_NAME = "ai_agent_interactions"

# Green API credentials
GREENAPI_BASE_URL = os.getenv("GREENAPI_BASE_URL", "https://api.green-api.com")
GREENAPI_INSTANCE = os.getenv("GREENAPI_INSTANCE")
GREENAPI_TOKEN = os.getenv("GREENAPI_TOKEN")


def get_or_create_conversation(db: Session, chat_id: str, sender_name: str = None, sender_phone: str = None) -> Conversation:
    """
    Get active conversation for chat_id or create new one.
    """
    # Check for active conversation
    conversation = db.query(Conversation).filter(
        Conversation.chat_id == chat_id,
        Conversation.status == "active"
    ).first()
    
    if not conversation:
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


def load_conversation_state(db: Session, conversation: Conversation) -> OrderState:
    """
    Load conversation history into OrderState.
    """
    # Get all messages for this conversation
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation.id
    ).order_by(ConversationMessage.timestamp.asc()).all()
    
    # Initialize state
    state = OrderState()
    state["chat_id"] = conversation.chat_id
    state["conversation_id"] = conversation.id
    state["current_step"] = conversation.current_step or "greet"
    state["started_at"] = conversation.created_at.isoformat()
    
    # Load message history
    state["messages"] = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    # Check if we have an existing AI order
    ai_order = db.query(AIGeneratedOrder).filter(
        AIGeneratedOrder.conversation_id == conversation.id
    ).first()
    
    if ai_order:
        # Load partial order data
        state["items"] = ai_order.items
        state["delivery_datetime"] = ai_order.estimated_delivery_datetime.isoformat() if ai_order.estimated_delivery_datetime else None
        state["delivery_address"] = ai_order.delivery_address
        state["payment_status"] = ai_order.payment_status
        state["client_name"] = ai_order.client_name
        state["client_phone"] = ai_order.client_phone
        state["additional_phone"] = ai_order.additional_phone
        state["notes"] = ai_order.notes
        
        # Set flags
        state["has_items"] = bool(ai_order.items)
        state["has_delivery_info"] = bool(ai_order.estimated_delivery_datetime)
        state["has_payment_info"] = bool(ai_order.payment_status)
        state["has_contact_info"] = bool(ai_order.client_name or ai_order.client_phone)
    
    return state


def save_conversation_state(db: Session, conversation: Conversation, state: OrderState):
    """
    Save conversation state to database.
    """
    # Update conversation
    conversation.current_step = state.get("current_step")
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
            timestamp=datetime.now()
        )
        db.add(conv_msg)
    
    # Save or update AI order
    ai_order = db.query(AIGeneratedOrder).filter(
        AIGeneratedOrder.conversation_id == conversation.id
    ).first()
    
    if not ai_order:
        ai_order = AIGeneratedOrder(
            conversation_id=conversation.id,
            chat_id=conversation.chat_id,
            validation_status="pending"
        )
        db.add(ai_order)
    
    # Update order data
    ai_order.items = state.get("items")
    ai_order.estimated_delivery_datetime = datetime.fromisoformat(state["delivery_datetime"]) if state.get("delivery_datetime") else None
    ai_order.delivery_address = state.get("delivery_address")
    ai_order.payment_status = state.get("payment_status")
    ai_order.client_name = state.get("client_name")
    ai_order.client_phone = state.get("client_phone")
    ai_order.additional_phone = state.get("additional_phone")
    ai_order.notes = state.get("notes")
    
    # If order confirmed, update status
    if state.get("order_confirmed"):
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
    
    if not chat_id:
        logger.error("No chat_id in message")
        return
    
    db = SessionLocal()
    try:
        # Get or create conversation
        conversation = get_or_create_conversation(db, chat_id, sender_name)
        
        # Load state
        state = load_conversation_state(db, conversation)
        
        # Add user message to state
        state["messages"].append({"role": "user", "content": message_text})
        state["last_user_message"] = message_text
        
        # If this is first message (greeting), invoke from start
        if state["current_step"] == "greet" and len(state["messages"]) == 1:
            # First interaction - run greeting
            result = order_graph.invoke(state)
        else:
            # Continue from current step
            result = order_graph.invoke(state)
        
        # Save updated state
        save_conversation_state(db, conversation, result)
        
        # Send response to WhatsApp
        assistant_message = result.get("last_assistant_message")
        if assistant_message:
            asyncio.run(send_whatsapp_message(chat_id, assistant_message))
        
        logger.info(f"Processed message for conversation {conversation.id}, step: {result.get('current_step')}")
        
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
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Set QoS
    channel.basic_qos(prefetch_count=1)
    
    # Start consuming
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )
    
    logger.info(f"Waiting for messages in queue: {QUEUE_NAME}")
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
