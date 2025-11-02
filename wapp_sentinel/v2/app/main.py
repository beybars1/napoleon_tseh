from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
import httpx
from dotenv import load_dotenv
import pika

# Load environment variables
load_dotenv()

app = FastAPI(title="Napoleon Tseh WhatsApp Service")

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

@app.post("/receiveNotification")
async def receive_notification(request: Request):
    """
    Endpoint to receive notifications from WhatsApp Green API
    """
    try:
        notification_data = await request.json()
        
        # Публикуем в RabbitMQ
        if publish_to_rabbitmq(notification_data):
            return {"status": "queued", "message": "Notification sent to processing queue"}
        else:
            raise HTTPException(status_code=500, detail="Failed to queue message")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
