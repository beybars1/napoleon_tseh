from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .database import get_db, Order
from ..services.greenapi_service import GreenAPIService
from ..processors.message_processor import MessageProcessor

app = FastAPI(title="Pastry Orders Automation")

# Initialize services
greenapi = GreenAPIService()
message_processor = MessageProcessor()

# Background scheduler
scheduler = BackgroundScheduler()

def process_incoming_messages():
    """Process incoming WhatsApp messages from main group"""
    try:
        print("Checking for notifications...")
        notification = greenapi.get_notification()
        
        if notification:
            print(f"Found notification: {notification}")
            
            # Process notification
            if "body" in notification and "messageData" in notification["body"]:
                message_data = notification["body"]["messageData"]
                
                # Only process messages from main group
                if message_data.get("chatId") == settings.MAIN_GROUP_CHAT_ID:
                    message_processor.process_message(message_data)
            
            # Delete notification
            greenapi.delete_notification(notification["receiptId"])
        
        # Check recent messages that might have been missed
        print("Checking recent messages...")
        recent_messages = greenapi.get_messages_by_date_range(
            chat_id=settings.MAIN_GROUP_CHAT_ID,
            start_date=datetime.now() - timedelta(hours=2)
        )
        
        for msg in recent_messages:
            message_processor.process_message(msg)
            
    except Exception as e:
        print(f"Error processing messages: {e}")

def send_daily_orders():
    """Send consolidated daily orders to operational group"""
    try:
        today = date.today().strftime("%Y-%m-%d")
        
        # Get unprocessed orders
        orders = message_processor.get_unprocessed_orders(today)
        
        if orders:
            # Send consolidated orders
            success = message_processor.consolidate_and_send_orders(
                orders=orders,
                target_chat_id=settings.OPERATIONAL_GROUP_CHAT_ID
            )
            
            if success:
                print(f"Sent daily orders: {len(orders)} orders")
            else:
                print("Failed to send daily orders")
        else:
            print("No orders for today")
            
    except Exception as e:
        print(f"Error sending daily orders: {e}")

# Schedule jobs
scheduler.add_job(
    send_daily_orders,
    CronTrigger(hour=settings.DAILY_ORDERS_HOUR, minute=0),
    id="daily_orders"
)

scheduler.add_job(
    process_incoming_messages,
    "interval",
    seconds=settings.MESSAGE_CHECK_INTERVAL,
    id="process_messages"
)

@app.on_event("startup")
async def startup_event():
    scheduler.start()
    print("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/")
async def root():
    return {"message": "Pastry Orders Automation API"}

@app.get("/orders")
async def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    return orders

@app.get("/orders/today")
async def get_today_orders(db: Session = Depends(get_db)):
    today = date.today().strftime("%Y-%m-%d")
    orders = db.query(Order).filter(Order.order_date == today).all()
    return orders

@app.get("/messages/chat/{chat_id}")
async def get_chat_messages(
    chat_id: str,
    days_back: int = 7,
    message_type: str = None
):
    """Get messages from a specific chat"""
    try:
        messages = greenapi.get_messages_by_date_range(
            chat_id=chat_id,
            start_date=datetime.now() - timedelta(days=days_back),
            message_type=message_type
        )
        
        return {
            "chat_id": chat_id,
            "total_messages": len(messages),
            "message_type": message_type,
            "days_analyzed": days_back,
            "messages": messages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/stats/{chat_id}")
async def get_chat_stats(chat_id: str, days: int = 7):
    """Get message statistics for a chat"""
    try:
        stats = greenapi.get_message_stats(chat_id, days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/bulk")
async def process_chat_history(
    background_tasks: BackgroundTasks,  # Moved to first position
    chat_id: str,
    days_back: int = 7,
    message_type: str = None
):
    """Process chat history in the background"""
    try:
        background_tasks.add_task(
            message_processor.process_chat_history,
            chat_id=chat_id,
            days_back=days_back,
            message_type=message_type
        )
        return {"message": f"Started processing messages from last {days_back} days"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-daily-orders")
async def trigger_daily_orders(background_tasks: BackgroundTasks):
    """Manually trigger daily orders sending"""
    background_tasks.add_task(send_daily_orders)
    return {"message": "Daily orders sending triggered"}

@app.post("/process-messages")
async def trigger_process_messages(background_tasks: BackgroundTasks):
    """Manually trigger message processing"""
    background_tasks.add_task(process_incoming_messages)
    return {"message": "Message processing triggered"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)