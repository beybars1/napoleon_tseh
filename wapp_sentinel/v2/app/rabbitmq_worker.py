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
ORDER_PROCESSING_QUEUE = os.getenv("ORDER_PROCESSING_QUEUE", "order_processing")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID", "120363403664602093@g.us")

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
# Объявляем очередь для обработки заказов
channel.queue_declare(queue=ORDER_PROCESSING_QUEUE, durable=True)

print(f"[*] Waiting for messages in queue '{RABBITMQ_QUEUE}'. To exit press CTRL+C")

def publish_to_order_queue(message_data: dict, table_name: str, message_id: int, timestamp: datetime, text: str, chat_id: str):
    """Publish message to order processing queue"""
    try:
        order_message = {
            'message_id': message_id,
            'message_table': table_name,
            'timestamp': timestamp.isoformat() if timestamp else None,
            'text': text,
            'chat_id': chat_id,
            'raw_data': message_data
        }
        
        channel.basic_publish(
            exchange='',
            routing_key=ORDER_PROCESSING_QUEUE,
            body=json.dumps(order_message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
            )
        )
        print(f"[→] Published to order queue: message_id={message_id}, table={table_name}")
        return True
    except Exception as e:
        print(f"[!] Error publishing to order queue: {e}")
        return False

def save_event_to_db(notification_data):
    """Save the incoming notification event to the database"""
    type_webhook = notification_data.get('typeWebhook')
    db = SessionLocal()
    msg = None
    table_name = None
    text = None
    
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
            table_name = 'outgoing_api_message'
            text = msg.text
            
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
            table_name = 'incoming_message'
            text = msg.text_message
            
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
            table_name = 'outgoing_message'
            text = msg.text
        
        if msg:
            db.commit()
            db.refresh(msg)  # Получаем ID сохраненного сообщения
            
            # Если это сообщение из целевого чата и есть текст, публикуем в order queue
            if text and msg.chat_id == TARGET_CHAT_ID and table_name:
                publish_to_order_queue(
                    message_data=notification_data,
                    table_name=table_name,
                    message_id=msg.id,
                    timestamp=msg.timestamp,
                    text=text,
                    chat_id=msg.chat_id
                )
            
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
