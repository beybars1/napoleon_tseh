from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
import json
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_db, Order
from openai_service import parse_order, consolidate_orders
from greenapi_service import send_message, get_notification, delete_notification, get_recent_messages, get_messages_bulk, get_all_available_messages, get_combined_messages, get_outgoing_messages

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

@app.get("/messages/all")
async def get_all_messages(
    chat_id: str = None,
    days_back: int = None,
    hours_back: int = None,
    max_messages: int = 1000,
    message_type: str = None  # 'incoming', 'outgoing', or None for all
):
    """
    Retrieve all messages from chat group - NO FILTERING BY DEFAULT
    """
    try:
        target_chat_id = chat_id or MAIN_GROUP_CHAT_ID
        
        if not target_chat_id:
            raise HTTPException(status_code=400, detail="No chat ID provided and MAIN_GROUP_CHAT_ID not configured")
        
        # GET RAW MESSAGES DIRECTLY FROM API - NO FILTERING
        print(f"🔥 Getting RAW messages directly from GreenAPI...")
        
        url = f"https://api.green-api.com/waInstance{os.getenv('GREEN_API_ID_INSTANCE')}/getChatHistory/{os.getenv('GREEN_API_TOKEN')}"
        
        payload = {
            "chatId": target_chat_id,
            "count": max_messages
        }
        
        import requests
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"GreenAPI error: {response.text}")
        
        messages = response.json() or []
        print(f"📥 Got {len(messages)} raw messages from API")
        
        # Show what we got BEFORE any filtering
        type_counts_raw = {}
        for msg in messages:
            msg_type = msg.get('type', 'unknown')
            type_counts_raw[msg_type] = type_counts_raw.get(msg_type, 0) + 1
        print(f"🔍 Raw message types: {type_counts_raw}")
        
        # ONLY filter by message type if requested, NOTHING ELSE
        if message_type and message_type in ['incoming', 'outgoing']:
            messages = [msg for msg in messages if msg.get('type') == message_type]
            print(f"🔽 Filtered to {message_type} only: {len(messages)} messages")
        
        # ONLY apply time filtering if explicitly requested
        if hours_back is not None or days_back is not None:
            cutoff_time = datetime.now()
            if hours_back is not None:
                cutoff_time = cutoff_time - timedelta(hours=hours_back)
            elif days_back is not None:
                cutoff_time = cutoff_time - timedelta(days=days_back)
            
            cutoff_timestamp = int(cutoff_time.timestamp())
            original_count = len(messages)
            messages = [msg for msg in messages if msg.get('timestamp', 0) >= cutoff_timestamp]
            print(f"⏰ Time filtered from {original_count} to {len(messages)} messages")
        
        # Prepare response
        response = {
            "chat_id": target_chat_id,
            "total_messages": len(messages),
            "filters_applied": {
                "days_back": days_back,
                "hours_back": hours_back,
                "message_type": message_type,
                "max_messages": max_messages
            },
            "message_breakdown": {
                "incoming": len([m for m in messages if m.get('type') == 'incoming']),
                "outgoing": len([m for m in messages if m.get('type') == 'outgoing']),
                "other": len([m for m in messages if m.get('type') not in ['incoming', 'outgoing']])
            },
            "raw_breakdown": type_counts_raw,
            "messages": messages
        }
        
        # Add date range info
        if messages:
            timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
            if timestamps:
                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)
                response["date_range"] = {
                    "oldest_message": datetime.fromtimestamp(oldest_ts).isoformat(),
                    "newest_message": datetime.fromtimestamp(newest_ts).isoformat(),
                    "span_days": (datetime.fromtimestamp(newest_ts) - datetime.fromtimestamp(oldest_ts)).days
                }
        
        return response
        
    except Exception as e:
        print(f"Error retrieving messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving messages: {str(e)}")

@app.get("/messages/summary")
async def get_messages_summary(
    chat_id: str = None,
    days_back: int = 7
):
    """
    Get a summary of messages without retrieving full message content
    Useful for quick statistics and overview
    """
    try:
        target_chat_id = chat_id or MAIN_GROUP_CHAT_ID
        
        if not target_chat_id:
            raise HTTPException(status_code=400, detail="No chat ID provided and MAIN_GROUP_CHAT_ID not configured")
        
        # Get messages for analysis
        messages = get_messages_bulk(target_chat_id, days_back, 1000)
        
        # Calculate statistics
        total_messages = len(messages)
        incoming_count = len([m for m in messages if m.get('type') == 'incoming'])
        outgoing_count = len([m for m in messages if m.get('type') == 'outgoing'])
        
        # Get date range
        date_info = {}
        if messages:
            timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
            if timestamps:
                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)
                date_info = {
                    "oldest_message": datetime.fromtimestamp(oldest_ts).isoformat(),
                    "newest_message": datetime.fromtimestamp(newest_ts).isoformat(),
                    "span_days": (datetime.fromtimestamp(newest_ts) - datetime.fromtimestamp(oldest_ts)).days
                }
        
        # Get message types breakdown
        message_types = {}
        for msg in messages:
            msg_type = msg.get('type', 'unknown')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        # Sample recent messages (last 5) for preview
        recent_messages = sorted(messages, key=lambda x: x.get('timestamp', 0), reverse=True)[:5]
        sample_messages = []
        for msg in recent_messages:
            sample_messages.append({
                "timestamp": datetime.fromtimestamp(msg.get('timestamp', 0)).isoformat() if msg.get('timestamp') else None,
                "type": msg.get('type'),
                "text_preview": msg.get('textMessage', '')[:100] + "..." if len(msg.get('textMessage', '')) > 100 else msg.get('textMessage', ''),
                "sender": msg.get('senderData', {}).get('sender', 'Unknown')
            })
        
        return {
            "chat_id": target_chat_id,
            "summary": {
                "total_messages": total_messages,
                "incoming_messages": incoming_count,
                "outgoing_messages": outgoing_count,
                "days_analyzed": days_back
            },
            "date_range": date_info,
            "message_types": message_types,
            "recent_messages_sample": sample_messages
        }
        
    except Exception as e:
        print(f"Error getting messages summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting messages summary: {str(e)}")

@app.get("/messages/outgoing")
async def get_outgoing_messages_only(
    chat_id: str = None,
    hours_back: int = 24
):
    """
    Get only outgoing messages (messages sent by you/your bakery)
    Useful for debugging and seeing what your system has sent
    """
    try:
        target_chat_id = chat_id or MAIN_GROUP_CHAT_ID
        
        if not target_chat_id:
            raise HTTPException(status_code=400, detail="No chat ID provided and MAIN_GROUP_CHAT_ID not configured")
        
        # Convert hours to minutes for the API
        minutes = hours_back * 60
        
        print(f"Retrieving outgoing messages from last {hours_back} hours...")
        outgoing_messages = get_outgoing_messages(target_chat_id, minutes)
        
        # Prepare response
        response = {
            "chat_id": target_chat_id,
            "total_outgoing_messages": len(outgoing_messages),
            "hours_analyzed": hours_back,
            "messages": outgoing_messages
        }
        
        # Add date range info if messages exist
        if outgoing_messages:
            timestamps = [msg.get('timestamp', 0) for msg in outgoing_messages if msg.get('timestamp')]
            if timestamps:
                oldest_ts = min(timestamps)
                newest_ts = max(timestamps)
                response["date_range"] = {
                    "oldest_message": datetime.fromtimestamp(oldest_ts).isoformat(),
                    "newest_message": datetime.fromtimestamp(newest_ts).isoformat(),
                    "span_hours": (datetime.fromtimestamp(newest_ts) - datetime.fromtimestamp(oldest_ts)).total_seconds() / 3600
                }
        
        return response
        
    except Exception as e:
        print(f"Error retrieving outgoing messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving outgoing messages: {str(e)}")

@app.get("/messages/debug")
async def debug_message_retrieval(chat_id: str = None):
    """
    Debug endpoint to test different message retrieval methods
    Shows what each method returns separately
    """
    try:
        target_chat_id = chat_id or MAIN_GROUP_CHAT_ID
        
        if not target_chat_id:
            raise HTTPException(status_code=400, detail="No chat ID provided and MAIN_GROUP_CHAT_ID not configured")
        
        print(f"🐛 Debug: Testing message retrieval methods for {target_chat_id}")
        
        # Test incoming messages (recent)
        print("Testing get_recent_messages...")
        incoming_recent = get_recent_messages(target_chat_id, 24)
        
        # Test outgoing messages
        print("Testing get_outgoing_messages...")
        outgoing_recent = get_outgoing_messages(target_chat_id, 1440)  # 24 hours in minutes
        
        # Test combined messages
        print("Testing get_combined_messages...")
        combined_messages = get_combined_messages(target_chat_id, 24)
        
        # Test all available messages
        print("Testing get_all_available_messages...")
        all_messages = get_all_available_messages(target_chat_id)
        
        return {
            "chat_id": target_chat_id,
            "debug_results": {
                "incoming_recent": {
                    "count": len(incoming_recent),
                    "method": "get_recent_messages(24h)",
                    "sample": incoming_recent[:2] if incoming_recent else []
                },
                "outgoing_recent": {
                    "count": len(outgoing_recent),
                    "method": "get_outgoing_messages(24h)",
                    "sample": outgoing_recent[:2] if outgoing_recent else []
                },
                "combined_messages": {
                    "count": len(combined_messages),
                    "method": "get_combined_messages(24h)",
                    "breakdown": {
                        "incoming": len([m for m in combined_messages if m.get('type') == 'incoming']),
                        "outgoing": len([m for m in combined_messages if m.get('type') == 'outgoing'])
                    }
                },
                "all_available": {
                    "count": len(all_messages),
                    "method": "get_all_available_messages()",
                    "breakdown": {
                        "incoming": len([m for m in all_messages if m.get('type') == 'incoming']),
                        "outgoing": len([m for m in all_messages if m.get('type') == 'outgoing'])
                    }
                }
            },
            "recommendation": "Use get_combined_messages() for recent data with both incoming/outgoing, or get_all_available_messages() for complete history"
        }
        
    except Exception as e:
        print(f"Error in debug endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@app.get("/messages/raw")
async def get_raw_messages(
    chat_id: str = None,
    count: int = 100
):
    """
    Get raw messages without any time filtering
    Useful for debugging timestamp issues
    """
    try:
        target_chat_id = chat_id or MAIN_GROUP_CHAT_ID
        
        if not target_chat_id:
            raise HTTPException(status_code=400, detail="No chat ID provided and MAIN_GROUP_CHAT_ID not configured")
        
        print(f"Getting raw messages for {target_chat_id} (count: {count})")
        
        # Get messages directly without any filtering
        url = f"https://api.green-api.com/waInstance{os.getenv('GREEN_API_ID_INSTANCE')}/getChatHistory/{os.getenv('GREEN_API_TOKEN')}"
        
        payload = {
            "chatId": target_chat_id,
            "count": count
        }
        
        import requests
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"GreenAPI error: {response.text}")
        
        messages = response.json() or []
        
        # Analyze timestamps
        now = datetime.now()
        timestamp_analysis = {
            "total_messages": len(messages),
            "messages_with_timestamps": 0,
            "timestamp_range": {},
            "type_breakdown": {},
            "recent_24h": 0,
            "recent_48h": 0,
            "recent_7d": 0
        }
        
        for msg in messages:
            msg_type = msg.get('type', 'unknown')
            timestamp_analysis["type_breakdown"][msg_type] = timestamp_analysis["type_breakdown"].get(msg_type, 0) + 1
            
            timestamp = msg.get('timestamp', 0)
            if timestamp:
                timestamp_analysis["messages_with_timestamps"] += 1
                msg_time = datetime.fromtimestamp(timestamp)
                hours_ago = (now - msg_time).total_seconds() / 3600
                
                if hours_ago <= 24:
                    timestamp_analysis["recent_24h"] += 1
                if hours_ago <= 48:
                    timestamp_analysis["recent_48h"] += 1
                if hours_ago <= 168:  # 7 days
                    timestamp_analysis["recent_7d"] += 1
        
        # Add timestamp range
        timestamps = [msg.get('timestamp', 0) for msg in messages if msg.get('timestamp')]
        if timestamps:
            oldest = min(timestamps)
            newest = max(timestamps)
            timestamp_analysis["timestamp_range"] = {
                "oldest": datetime.fromtimestamp(oldest).isoformat(),
                "newest": datetime.fromtimestamp(newest).isoformat(),
                "span_hours": (newest - oldest) / 3600
            }
        
        # Sample messages from each type
        samples = {}
        for msg_type in timestamp_analysis["type_breakdown"].keys():
            type_msgs = [msg for msg in messages if msg.get('type') == msg_type][:3]
            samples[msg_type] = []
            for msg in type_msgs:
                timestamp = msg.get('timestamp', 0)
                samples[msg_type].append({
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat() if timestamp else "No timestamp",
                    "text_preview": str(msg.get('textMessage', ''))[:50] + "..." if len(str(msg.get('textMessage', ''))) > 50 else str(msg.get('textMessage', '')),
                    "hours_ago": (now - datetime.fromtimestamp(timestamp)).total_seconds() / 3600 if timestamp else None
                })
        
        return {
            "chat_id": target_chat_id,
            "analysis": timestamp_analysis,
            "samples_by_type": samples,
            "raw_messages": messages[:10] if len(messages) > 10 else messages  # First 10 for debugging
        }
        
    except Exception as e:
        print(f"Error getting raw messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting raw messages: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)