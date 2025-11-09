from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import date, datetime
import os
import json
import httpx
from dotenv import load_dotenv
import pika
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Import database dependencies
from app.database.database import SessionLocal
from app.services.daily_report_service import DailyReportService
from app.scheduler import scheduler_instance


# Lifespan context manager для запуска/остановки scheduler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler_instance.start()
    yield
    # Shutdown
    scheduler_instance.stop()


app = FastAPI(
    title="Napoleon Tseh WhatsApp Service",
    lifespan=lifespan
)

# Get Green API base URL from environment variables
GREEN_API_BASE_URL = os.getenv("GREEN_API_BASE_URL", "https://api.green-api.com")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "greenapi_notifications")


# Pydantic модель для валидации входящих данных
class WhatsAppNotificationSchema(BaseModel):
    receiptId: int
    body: Dict[str, Any]

class SendMessageRequest(BaseModel):
    """Pydantic model for sending message request"""
    chatId: str
    message: str

class DailyReportRequest(BaseModel):
    """Pydantic model for daily report request"""
    date: str  # Format: YYYY-MM-DD
    chat_id: str
    
class DailyReportPreviewRequest(BaseModel):
    """Pydantic model for daily report preview"""
    date: str  # Format: YYYY-MM-DD

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/sendMessage")
async def send_message(message_request: SendMessageRequest):
    """
    Send a message via Green API
    
    Args:
        message_request: SendMessageRequest containing chatId and message
    
    Returns:
        Dict: Response from Green API about message status
    """
    instance_id = os.getenv("GREENAPI_INSTANCE")
    token = os.getenv("GREENAPI_TOKEN")
    
    if not instance_id or not token:
        raise HTTPException(
            status_code=500,
            detail="Environment variables GREENAPI_INSTANCE and GREENAPI_TOKEN must be set"
        )
    
    # Construct Green API URL for sending message
    send_url = f"{GREEN_API_BASE_URL}/waInstance{instance_id}/sendMessage/{token}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                send_url,
                json={
                    "chatId": message_request.chatId,
                    "message": message_request.message
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Green API request failed: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Green API: {str(e)}"
        )

@app.delete("/removeNotification/{receipt_id}")
async def remove_notification(receipt_id: int):
    """
    Delete a specific notification from Green API by receipt ID
    
    Args:
        receipt_id (int): The ID of the notification to delete
    
    Returns:
        Dict: Response from Green API about deletion status
    """
    instance_id = os.getenv("GREENAPI_INSTANCE")
    token = os.getenv("GREENAPI_TOKEN")
    
    if not instance_id or not token:
        raise HTTPException(
            status_code=500,
            detail="Environment variables GREENAPI_INSTANCE and GREENAPI_TOKEN must be set"
        )
    
    # Construct Green API URL for deletion
    delete_url = f"{GREEN_API_BASE_URL}/waInstance{instance_id}/deleteNotification/{token}/{receipt_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(delete_url)
            response.raise_for_status()
            return response.json()
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Green API request failed: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Green API: {str(e)}"
        )

def publish_to_rabbitmq(message: dict):
    """Publish message to RabbitMQ queue"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"),
            os.getenv("RABBITMQ_PASSWORD", "guest")
        )
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # делаем сообщение persistent
            )
        )
        
        connection.close()
        return True
    except Exception as e:
        print(f"Error publishing to RabbitMQ: {e}")
        return False


def publish_to_ai_agent_queue(message: dict):
    """Publish message to AI agent interactions queue"""
    try:
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"),
            os.getenv("RABBITMQ_PASSWORD", "guest")
        )
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        ai_queue = "ai_agent_interactions"
        channel.queue_declare(queue=ai_queue, durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key=ai_queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        
        connection.close()
        return True
    except Exception as e:
        print(f"Error publishing to AI agent queue: {e}")
        return False


def determine_message_type(notification_data: dict) -> str:
    """
    Determine if message is from manager (for order processing) or client (for AI agent).
    
    Returns:
        "manager" - route to order_processing queue (existing flow)
        "client" - route to ai_agent_interactions queue (new AI agent)
    """
    try:
        # Green API может присылать данные либо в body, либо на верхнем уровне
        type_webhook = notification_data.get("typeWebhook", "")
        
        # Only process incoming text messages
        if type_webhook != "incomingMessageReceived":
            return "manager"  # Default to manager for non-message webhooks
        
        message_data = notification_data.get("messageData", {})
        type_message = message_data.get("typeMessage", "")
        
        # Accept both textMessage and extendedTextMessage (with links, quotes, etc.)
        if type_message not in ["textMessage", "extendedTextMessage"]:
            return "manager"  # Non-text messages go to manager
        
        # Get chat_id to identify sender
        sender_data = notification_data.get("senderData", {})
        chat_id = sender_data.get("chatId", "")
        
        print(f"[DEBUG] chat_id from message: {chat_id}")
        
        # Define manager chat IDs
        manager_chat_ids = os.getenv("MANAGER_CHAT_IDS", "").split(",")
        manager_chat_ids = [cid.strip() for cid in manager_chat_ids if cid.strip()]
        
        # Define AI agent whitelist (for testing)
        ai_agent_chat_ids = os.getenv("AI_AGENT_CHAT_IDS", "").split(",")
        ai_agent_chat_ids = [cid.strip() for cid in ai_agent_chat_ids if cid.strip()]
        
        print(f"[DEBUG] Manager chat IDs: {manager_chat_ids}")
        print(f"[DEBUG] AI Agent whitelist: {ai_agent_chat_ids}")
        
        # If from manager, route to existing order processing
        if chat_id in manager_chat_ids:
            print(f"[DEBUG] Manager detected - routing to ORDER PROCESSING")
            return "manager"
        
        # If in AI agent whitelist, route to AI agent
        if chat_id in ai_agent_chat_ids:
            print(f"[DEBUG] AI whitelist match - routing to AI AGENT")
            return "client"
        
        # Otherwise, default to manager (ignore unknown chats)
        print(f"[DEBUG] Unknown chat - routing to MANAGER (ignored)")
        return "manager"
        
    except Exception as e:
        print(f"Error determining message type: {e}")
        return "manager"  # Default to manager on error

@app.post("/receiveNotification")
async def receive_notification(request: Request):
    """
    Endpoint to receive notifications from WhatsApp Green API.
    Routes messages to appropriate queue based on sender.
    """
    try:
        notification_data = await request.json()
        
        # Determine message type and route accordingly
        message_type = determine_message_type(notification_data)
        
        print(f"[ROUTING] Message type determined: {message_type}")
        print(f"[ROUTING] Notification data: {json.dumps(notification_data, indent=2)}")
        
        if message_type == "client":
            # Extract message data for AI agent
            message_data = notification_data.get("messageData", {})
            sender_data = notification_data.get("senderData", {})
            
            # Extract text from either textMessage or extendedTextMessage
            text = ""
            if "textMessageData" in message_data:
                text = message_data.get("textMessageData", {}).get("textMessage", "")
            elif "extendedTextMessageData" in message_data:
                text = message_data.get("extendedTextMessageData", {}).get("text", "")
            
            ai_message = {
                "chat_id": sender_data.get("chatId", ""),
                "sender_name": sender_data.get("senderName", ""),
                "text": text,
                "timestamp": notification_data.get("timestamp"),
                "raw_data": notification_data
            }
            
            if publish_to_ai_agent_queue(ai_message):
                return {
                    "status": "queued",
                    "message": "Client message sent to AI agent",
                    "route": "ai_agent"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to queue AI agent message")
        else:
            # Manager message - use existing flow
            if publish_to_rabbitmq(notification_data):
                return {
                    "status": "queued",
                    "message": "Manager message sent to processing queue",
                    "route": "order_processing"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to queue message")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orders/send-daily-report")
async def send_daily_report(
    request: DailyReportRequest,
    db: Session = Depends(get_db)
):
    """
    Send daily order report to specified WhatsApp chat
    
    Args:
        request: DailyReportRequest with date and chat_id
        db: Database session
        
    Returns:
        Status of report generation and sending
    """
    try:
        # Парсим дату
        target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        service = DailyReportService(db)
        result = await service.generate_and_send_report(target_date, request.chat_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate/send report: {str(e)}"
        )


@app.post("/orders/preview-daily-report")
async def preview_daily_report(
    request: DailyReportPreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Preview daily order report without sending to WhatsApp
    
    Args:
        request: DailyReportPreviewRequest with date
        db: Database session
        
    Returns:
        Formatted report text and order count
    """
    try:
        # Парсим дату
        target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        service = DailyReportService(db)
        orders = service.get_orders_for_date(target_date)
        report_text = service.format_report(orders, target_date)
        
        return {
            "status": "success",
            "date": target_date.isoformat(),
            "orders_count": len(orders),
            "report_preview": report_text
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )


@app.get("/orders/daily-report/{date_str}")
async def get_daily_report_quick(
    date_str: str,
    db: Session = Depends(get_db)
):
    """
    Quick GET endpoint to preview daily report
    
    Args:
        date_str: Date in format YYYY-MM-DD
        db: Database session
        
    Returns:
        Formatted report preview
    """
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        service = DailyReportService(db)
        orders = service.get_orders_for_date(target_date)
        report_text = service.format_report(orders, target_date)
        
        return {
            "date": target_date.isoformat(),
            "orders_count": len(orders),
            "report": report_text
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@app.get("/scheduler/status")
async def get_scheduler_status():
    """
    Get scheduler status and configuration
    
    Returns:
        Scheduler status including next run time
    """
    return scheduler_instance.get_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
