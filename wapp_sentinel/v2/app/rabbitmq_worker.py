import pika
import os
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from app.database.database import SessionLocal
from app.database.models import (
    OutgoingAPIMessage, IncomingMessage, IncomingCall,
    OutgoingMessage, OutgoingMessageStatus
)

def get_timestamp(ts):
    """Convert Unix timestamp to datetime"""
    try:
        if not ts:
            return None
        timestamp = int(ts)
        # Используем fromtimestamp, так как timestamp от Green API уже в UTC
        return datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError) as e:
        print(f"Error converting timestamp {ts}: {e}")
        return None

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "greenapi_notifications")

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

print(f"[*] Waiting for messages in queue '{RABBITMQ_QUEUE}'. To exit press CTRL+C")

def save_event_to_db(notification_data):
    """Save the incoming notification event to the database"""
    type_webhook = notification_data.get('typeWebhook')
    db = SessionLocal()
    msg = None
    try:
        if type_webhook == "outgoingAPIMessageReceived":
            msg = OutgoingAPIMessage(
                receipt_id=notification_data.get('receiptId'),
                id_message=notification_data.get('idMessage'),
                timestamp=get_timestamp(notification_data.get('timestamp')),
                chat_id=notification_data.get('senderData', {}).get('chatId'),
                sender=notification_data.get('senderData', {}).get('sender'),
                chat_name=notification_data.get('senderData', {}).get('chatName'),
                sender_name=notification_data.get('senderData', {}).get('senderName'),
                text=notification_data.get('messageData', {}).get('textMessageData', {}).get('textMessage'),
                raw_data=notification_data
            )
            db.add(msg)
        elif type_webhook == "incomingMessageReceived":
            msg = IncomingMessage(
                receipt_id=notification_data.get('receiptId'),
                id_message=notification_data.get('idMessage'),
                timestamp=get_timestamp(notification_data.get('timestamp')),
                chat_id=notification_data.get('senderData', {}).get('chatId'),
                sender=notification_data.get('senderData', {}).get('sender'),
                chat_name=notification_data.get('senderData', {}).get('chatName'),
                sender_name=notification_data.get('senderData', {}).get('senderName'),
                sender_contact_name=notification_data.get('senderData', {}).get('senderContactName'),
                type_message=notification_data.get('messageData', {}).get('typeMessage'),
                text_message=notification_data.get('messageData', {}).get('textMessageData', {}).get('textMessage'),
                type_webhook=notification_data.get('typeWebhook'),
                raw_data=notification_data
            )
            db.add(msg)
        elif type_webhook == "outgoingMessageStatus":
            msg = OutgoingMessageStatus(
                receipt_id=notification_data.get('receiptId'),
                chat_id=notification_data.get('chatId'),
                status=notification_data.get('status'),
                id_message=notification_data.get('idMessage'),
                send_by_api=notification_data.get('sendByApi'),
                timestamp=get_timestamp(notification_data.get('timestamp')),
                raw_data=notification_data
            )
            db.add(msg)
        elif type_webhook == "outgoingMessageReceived":
            msg = OutgoingMessage(
                receipt_id=notification_data.get('receiptId'),
                id_message=notification_data.get('idMessage'),
                timestamp=get_timestamp(notification_data.get('timestamp')),
                chat_id=notification_data.get('senderData', {}).get('chatId'),
                sender=notification_data.get('senderData', {}).get('sender'),
                chat_name=notification_data.get('senderData', {}).get('chatName'),
                sender_name=notification_data.get('senderData', {}).get('senderName'),
                text=notification_data.get('messageData', {}).get('textMessageData', {}).get('textMessage'),
                raw_data=notification_data
            )
            db.add(msg)
        
        if msg:
            db.commit()
            return True
    except Exception as e:
        db.rollback()
        print(f"Error saving to database: {e}")
        return False
    finally:
        db.close()

def callback(ch, method, properties, body):
    print(f"[x] Received message: {body}")
    try:
        # Преобразуем JSON в dict
        notification_data = json.loads(body.decode())
        save_event_to_db(notification_data)
        print("[+] Saved to DB")
    except Exception as e:
        print(f"[!] Error processing message: {e}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)

channel.start_consuming()
