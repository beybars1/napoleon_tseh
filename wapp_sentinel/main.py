from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_db, Order
from openai_service import parse_order, consolidate_orders
from greenapi_service import send_message, get_notification, delete_notification, get_recent_messages, get_messages_bulk

app = FastAPI(title="Pastry Orders Automation")

MAIN_GROUP_CHAT_ID = os.getenv("MAIN_GROUP_CHAT_ID")
OPERATIONAL_GROUP_CHAT_ID = os.getenv("OPERATIONAL_GROUP_CHAT_ID")

# Background scheduler for daily consolidation
scheduler = BackgroundScheduler()

def process_incoming_messages():
    """Process incoming WhatsApp messages from main group"""
    db = next(get_db())
    
    try:
        print("Checking for notifications...")
        notification = get_notification()
        
        if notification:
            print(f"Found notification: {notification}")
            
            # Process notification
            if "body" in notification and "messageData" in notification["body"]:
                message_data = notification["body"]["messageData"]
                
                # Only process messages from main group
                if message_data.get("chatId") == MAIN_GROUP_CHAT_ID:
                    # Check if already processed
                    existing = db.query(Order).filter(
                        Order.message_id == message_data.get("idMessage")
                    ).first()
                    
                    if not existing:
                        # Parse message with OpenAI
                        message_text = message_data.get("textMessageData", {}).get("textMessage", "")
                        if message_text:
                            parsed_data = parse_order(message_text)
                            
                            # Save to database
                            order = Order(
                                message_id=message_data.get("idMessage"),
                                chat_id=message_data.get("chatId"),
                                sender=message_data.get("senderData", {}).get("sender", ""),
                                raw_message=message_text,
                                parsed_data=json.dumps(parsed_data),
                                order_date=parsed_data.get("order_date") if parsed_data.get("is_order") else None,
                                customer_name=parsed_data.get("customer_name") if parsed_data.get("is_order") else None,
                                total_amount=parsed_data.get("total_amount") if parsed_data.get("is_order") else None,
                                delivery_time=parsed_data.get("delivery_time") if parsed_data.get("is_order") else None,
                                processed=not parsed_data.get("is_order", False)
                            )
                            
                            db.add(order)
                            db.commit()
                            
                            print(f"Processed message: {'ORDER' if parsed_data.get('is_order', False) else 'NON-ORDER'}")
                
            # Delete notification
            delete_notification(notification["receiptId"])
        else:
            print("No new notifications")
        
        # Also check recent messages that might have been missed (both incoming and outgoing)
        print("Checking recent messages...")
        recent_messages = get_recent_messages(MAIN_GROUP_CHAT_ID, hours_back=2)
        
        for msg in recent_messages:
            msg_id = msg.get('idMessage')
            message_text = msg.get('textMessage', '')
            
            # Process both incoming and outgoing messages (manager posts orders)
            if msg_id and message_text:
                # Check if already processed
                existing = db.query(Order).filter(Order.message_id == msg_id).first()
                
                if not existing:
                    parsed_data = parse_order(message_text)
                    
                    order = Order(
                        message_id=msg_id,
                        chat_id=MAIN_GROUP_CHAT_ID,
                        sender=msg.get('senderData', {}).get('sender', ''),
                        raw_message=message_text,
                        parsed_data=json.dumps(parsed_data),
                        order_date=parsed_data.get("order_date") if parsed_data.get("is_order") else None,
                        customer_name=parsed_data.get("customer_name") if parsed_data.get("is_order") else None,
                        total_amount=parsed_data.get("total_amount") if parsed_data.get("is_order") else None,
                        delivery_time=parsed_data.get("delivery_time") if parsed_data.get("is_order") else None,
                        processed=not parsed_data.get("is_order", False)
                    )
                    
                    db.add(order)
                    db.commit()
                    msg_type = msg.get('type', 'unknown')
                    print(f"Processed recent message ({msg_type}): {'ORDER' if parsed_data.get('is_order', False) else 'NON-ORDER'}")
        
    except Exception as e:
        print(f"Error processing messages: {e}")
    finally:
        db.close()

def bulk_process_historical_messages(days_back: int = 7):
    """Bulk process historical messages from last N days"""
    db = next(get_db())
    
    try:
        print(f"🔄 Starting bulk processing for last {days_back} days...")
        
        # Get all messages from specified days back
        messages = get_messages_bulk(MAIN_GROUP_CHAT_ID, days_back)
        
        if not messages:
            print("❌ No messages found to process")
            return
        
        processed_count = 0
        order_count = 0
        skipped_count = 0
        
        print(f"📋 Processing {len(messages)} messages...")
        
        for msg in messages:
            try:
                msg_id = msg.get('idMessage')
                msg_text = msg.get('textMessage', '')
                msg_type = msg.get('type', '')
                
                # Skip if no message ID or text
                if not msg_id or not msg_text:
                    skipped_count += 1
                    continue
                
                # Process BOTH incoming and outgoing messages (manager posts orders)
                
                # Check if already processed
                existing = db.query(Order).filter(Order.message_id == msg_id).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Parse with OpenAI
                parsed_data = parse_order(msg_text)
                
                # Create order record
                order = Order(
                    message_id=msg_id,
                    chat_id=MAIN_GROUP_CHAT_ID,
                    sender=msg.get('senderData', {}).get('sender', ''),
                    raw_message=msg_text,
                    parsed_data=json.dumps(parsed_data),
                    order_date=parsed_data.get("order_date") if parsed_data.get("is_order") else None,
                    customer_name=parsed_data.get("customer_name") if parsed_data.get("is_order") else None,
                    total_amount=parsed_data.get("total_amount") if parsed_data.get("is_order") else None,
                    delivery_time=parsed_data.get("delivery_time") if parsed_data.get("is_order") else None,
                    processed=not parsed_data.get("is_order", False)
                )
                
                db.add(order)
                db.commit()
                
                if parsed_data.get("is_order"):
                    order_count += 1
                    print(f"✅ ORDER: {parsed_data.get('customer_name', 'Unknown')} - {parsed_data.get('order_date')}")
                
                processed_count += 1
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                continue
        
        print(f"🎉 Bulk processing complete!")
        print(f"   📥 Messages processed: {processed_count}")
        print(f"   🛒 Orders found: {order_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        
    except Exception as e:
        print(f"❌ Bulk processing error: {e}")
    finally:
        db.close()

def send_daily_orders():
    """Send consolidated daily orders to operational group"""
    db = next(get_db())
    today = date.today().strftime("%Y-%m-%d")
    
    try:
        # Get today's unprocessed orders
        orders = db.query(Order).filter(
            Order.order_date == today,
            Order.processed == False
        ).all()
        
        if not orders:
            print("No orders for today")
            return
        
        # Prepare orders data
        orders_data = []
        for order in orders:
            parsed = json.loads(order.parsed_data)
            if parsed.get("is_order"):
                orders_data.append(parsed)
        
        if not orders_data:
            print("No valid orders for today")
            return
        
        # Generate consolidated message
        consolidated_message = consolidate_orders(orders_data, today)
        
        # Send to operational group
        result = send_message(OPERATIONAL_GROUP_CHAT_ID, consolidated_message)
        
        if "error" not in result:
            # Mark orders as processed
            for order in orders:
                order.processed = True
            db.commit()
            print(f"Sent daily orders: {len(orders_data)} orders")
        else:
            print(f"Failed to send daily orders: {result}")
            
    except Exception as e:
        print(f"Error sending daily orders: {e}")
    finally:
        db.close()

# Schedule daily orders at 8 AM
# scheduler.add_job(
#     send_daily_orders,
#     CronTrigger(hour=8, minute=0),
#     id="daily_orders"
# )

# # Process messages every 30 seconds
# scheduler.add_job(
#     process_incoming_messages,
#     "interval",
#     seconds=30,
#     id="process_messages"
# )

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

@app.post("/bulk-process-messages")
async def trigger_bulk_process(background_tasks: BackgroundTasks, days: int = 7):
    """Bulk process messages from last N days"""
    background_tasks.add_task(bulk_process_historical_messages, days)
    return {"message": f"Bulk processing triggered for last {days} days"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)