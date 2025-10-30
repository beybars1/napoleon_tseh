from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import httpx
from dotenv import load_dotenv
from app.database import WhatsAppNotification, SessionLocal
from app.database.models import (
    OutgoingAPIMessage, IncomingMessage, IncomingCall,
    OutgoingMessage, OutgoingMessageStatus
)
from app.database.database import SessionLocal
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="WhatsApp Notification Service")

# Get Green API base URL from environment variables
GREEN_API_BASE_URL = os.getenv("GREEN_API_BASE_URL", "https://api.green-api.com")


# Pydantic модель для валидации входящих данных
class WhatsAppNotificationSchema(BaseModel):
    receiptId: int
    body: Dict[str, Any]

class SendMessageRequest(BaseModel):
    """Pydantic model for sending message request"""
    chatId: str
    message: str

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

def save_event_to_db(notification_data):
    """
    Save the incoming notification event to the database
    
    Args:
        notification_data (dict): The notification data from Green API
    """
    body = notification_data.get('body', {})
    type_webhook = body.get('typeWebhook')
    db = SessionLocal()
    try:
        if type_webhook == "outgoingAPIMessageReceived":
            msg = OutgoingAPIMessage(
                receipt_id=notification_data.get('receiptId'),
                id_message=body.get('idMessage'),
                timestamp=datetime.fromtimestamp(body.get('timestamp')) if body.get('timestamp') else None,
                chat_id=body.get('senderData', {}).get('chatId'),
                sender=body.get('senderData', {}).get('sender'),
                chat_name=body.get('senderData', {}).get('chatName'),
                sender_name=body.get('senderData', {}).get('senderName'),
                text=body.get('messageData', {}).get('extendedTextMessageData', {}).get('text'),
                raw_data=notification_data
            )
            db.add(msg)
        elif type_webhook == "incomingMessageReceived":
            msg = IncomingMessage(
                receipt_id=notification_data.get('receiptId'),
                id_message=body.get('idMessage'),
                timestamp=datetime.fromtimestamp(body.get('timestamp')) if body.get('timestamp') else None,
                chat_id=body.get('senderData', {}).get('chatId'),
                sender=body.get('senderData', {}).get('sender'),
                chat_name=body.get('senderData', {}).get('chatName'),
                sender_name=body.get('senderData', {}).get('senderName'),
                sender_contact_name=body.get('senderData', {}).get('senderContactName'),
                type_message=body.get('messageData', {}).get('typeMessage'),
                text_message=body.get('messageData', {}).get('textMessageData', {}).get('textMessage'),
                type_webhook=body.get('typeWebhook'),
                deleted_message_type=body.get('messageData', {}).get('deletedMessageData', {}).get('typeMessage'),
                deleted_message_stanza_id=body.get('messageData', {}).get('deletedMessageData', {}).get('stanzaId'),
                raw_data=notification_data
            )
            db.add(msg)
        elif type_webhook == "incomingCall":
            msg = IncomingCall(
                receipt_id=notification_data.get('receiptId'),
                from_id=body.get('from'),
                status=body.get('status'),
                id_message=body.get('idMessage'),
                timestamp=datetime.fromtimestamp(body.get('timestamp')) if body.get('timestamp') else None,
                raw_data=notification_data
            )
            db.add(msg)
        elif type_webhook == "outgoingMessageReceived":
            msg = OutgoingMessage(
                receipt_id=notification_data.get('receiptId'),
                id_message=body.get('idMessage'),
                timestamp=datetime.fromtimestamp(body.get('timestamp')) if body.get('timestamp') else None,
                chat_id=body.get('senderData', {}).get('chatId'),
                sender=body.get('senderData', {}).get('sender'),
                chat_name=body.get('senderData', {}).get('chatName'),
                sender_name=body.get('senderData', {}).get('senderName'),
                text=body.get('messageData', {}).get('textMessageData', {}).get('textMessage'),
                raw_data=notification_data
            )
            db.add(msg)
        elif type_webhook == "outgoingMessageStatus":
            msg = OutgoingMessageStatus(
                receipt_id=notification_data.get('receiptId'),
                chat_id=body.get('chatId'),
                status=body.get('status'),
                id_message=body.get('idMessage'),
                send_by_api=body.get('sendByApi'),
                timestamp=datetime.fromtimestamp(body.get('timestamp')) if body.get('timestamp') else None,
                raw_data=notification_data
            )
            db.add(msg)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving event: {e}")
    finally:
        db.close()

async def process_and_delete_notification(notification_data: Dict[str, Any]):
    """
    Process the notification and then delete it from Green API
    
    Args:
        notification_data: The notification data from Green API
    """
    if not notification_data:
        return
        
    receipt_id = notification_data.get("receiptId")
    if not receipt_id:
        return
        
    # Сохраняем событие в нужную таблицу
    save_event_to_db(notification_data)
    
    # Delete from Green API
    instance_id = os.getenv("GREENAPI_INSTANCE")
    token = os.getenv("GREENAPI_TOKEN")
    delete_url = f"{GREEN_API_BASE_URL}/waInstance{instance_id}/deleteNotification/{token}/{receipt_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            await client.delete(delete_url)
    except Exception as e:
        print(f"Error deleting notification: {e}")

@app.get("/receiveNotification")
async def receive_notification(
    background_tasks: BackgroundTasks,
    receive_timeout: Optional[int] = 5
):
    """
    Endpoint to receive notifications from WhatsApp Green API
    
    Args:
        background_tasks: FastAPI background tasks
        receive_timeout (int, optional): Timeout in seconds. Defaults to 5.
    
    Returns:
        Dict: Notification data from Green API
    """
    instance_id = os.getenv("GREENAPI_INSTANCE")
    token = os.getenv("GREENAPI_TOKEN")
    
    if not instance_id or not token:
        raise HTTPException(
            status_code=500,
            detail="Environment variables GREENAPI_INSTANCE and GREENAPI_TOKEN must be set"
        )
    
    # Construct Green API URL
    green_api_url = f"{GREEN_API_BASE_URL}/waInstance{instance_id}/receiveNotification/{token}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                green_api_url,
                params={"receiveTimeout": receive_timeout},
                timeout=receive_timeout + 5  # Add small buffer to client timeout
            )
            response.raise_for_status()
            notification_data = response.json()
            
            if notification_data:
                # Запускаем обработку и удаление уведомления в фоновом режиме
                background_tasks.add_task(process_and_delete_notification, notification_data)
                
            return notification_data
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
