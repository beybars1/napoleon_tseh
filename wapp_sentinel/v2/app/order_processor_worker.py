import pika
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from app.database.database import SessionLocal
from app.database.models import Order, IncomingMessage, OutgoingMessage, OutgoingAPIMessage
from app.services.openai_service import OpenAIOrderParser

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
ORDER_PROCESSING_QUEUE = os.getenv("ORDER_PROCESSING_QUEUE", "order_processing")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# Инициализируем OpenAI parser
openai_parser = OpenAIOrderParser()

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    credentials=credentials
))
channel = connection.channel()
channel.queue_declare(queue=ORDER_PROCESSING_QUEUE, durable=True)

print(f"[*] Order Processor Worker started")
print(f"[*] Waiting for messages in queue '{ORDER_PROCESSING_QUEUE}'. To exit press CTRL+C")


def parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """Parse datetime string from OpenAI response"""
    if not dt_string:
        return None
    
    try:
        # Пытаемся распарсить в формате "YYYY-MM-DD HH:MM:SS"
        return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            # Пытаемся распарсить в формате "YYYY-MM-DD"
            return datetime.strptime(dt_string, "%Y-%m-%d")
        except ValueError:
            print(f"[!] Failed to parse datetime: {dt_string}")
            return None


def check_if_already_processed(message_id: int, message_table: str) -> bool:
    """Check if message was already processed"""
    db = SessionLocal()
    try:
        existing_order = db.query(Order).filter(
            Order.message_id == message_id,
            Order.message_table == message_table
        ).first()
        return existing_order is not None
    finally:
        db.close()


def mark_message_as_processed(message_id: int, message_table: str) -> bool:
    """Mark original message as processed"""
    db = SessionLocal()
    try:
        if message_table == 'incoming_message':
            msg = db.query(IncomingMessage).filter(IncomingMessage.id == message_id).first()
        elif message_table == 'outgoing_message':
            msg = db.query(OutgoingMessage).filter(OutgoingMessage.id == message_id).first()
        elif message_table == 'outgoing_api_message':
            msg = db.query(OutgoingAPIMessage).filter(OutgoingAPIMessage.id == message_id).first()
        else:
            print(f"[!] Unknown message table: {message_table}")
            return False
        
        if msg:
            msg.order_processed = True
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"[!] Error marking message as processed: {e}")
        return False
    finally:
        db.close()


def process_order_message(order_data: dict):
    """Process order message from queue"""
    message_id = order_data.get('message_id')
    message_table = order_data.get('message_table')
    text = order_data.get('text')
    chat_id = order_data.get('chat_id')
    timestamp_str = order_data.get('timestamp')
    
    if not all([message_id, message_table, text, chat_id]):
        print(f"[!] Missing required fields in order data")
        return False
    
    print(f"[→] Processing order: message_id={message_id}, table={message_table}")
    
    # Проверяем, не обработано ли уже
    if check_if_already_processed(message_id, message_table):
        print(f"[i] Order already processed, skipping")
        return True
    
    # Парсим timestamp
    try:
        order_accepted_date = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
    except:
        order_accepted_date = datetime.now()
    
    # Парсим заказ через OpenAI
    print(f"[AI] Sending to OpenAI for parsing...")
    parsed_data = openai_parser.parse_order_message(text)
    print(f"[AI] OpenAI response confidence: {parsed_data.get('confidence', 'unknown')}")
    
    # Создаем Order запись
    db = SessionLocal()
    try:
        order = Order(
            message_id=message_id,
            message_table=message_table,
            chat_id=chat_id,
            order_accepted_date=order_accepted_date,
            estimated_delivery_datetime=parse_datetime(parsed_data.get('estimated_delivery_datetime')),
            payment_status=parsed_data.get('payment_status'),
            contact_number_primary=parsed_data.get('contact_number_primary'),
            contact_number_secondary=parsed_data.get('contact_number_secondary'),
            items=parsed_data.get('items', []),
            client_name=parsed_data.get('client_name'),
            raw_message_text=text,
            openai_response=parsed_data,
            confidence=parsed_data.get('confidence', 'low'),
            processing_status='completed'
        )
        
        db.add(order)
        db.commit()
        
        print(f"[✓] Order saved to database: order_id={order.id}")
        
        # Помечаем исходное сообщение как обработанное
        if mark_message_as_processed(message_id, message_table):
            print(f"[✓] Message marked as processed")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[!] Error saving order: {e}")
        return False
    finally:
        db.close()


def callback(ch, method, properties, body):
    """Callback for processing messages from queue"""
    print(f"\n[x] Received order message")
    
    try:
        order_data = json.loads(body.decode())
        
        if process_order_message(order_data):
            print(f"[✓] Order processed successfully")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print(f"[!] Order processing failed, rejecting message")
            # Отклоняем сообщение, не возвращаем в очередь
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
    except json.JSONDecodeError as e:
        print(f"[!] Invalid JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f"[!] Error processing order: {e}")
        # В случае неожиданной ошибки, возвращаем в очередь для повторной попытки
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


# Настройка обработки сообщений
channel.basic_qos(prefetch_count=1)  # Обрабатываем по одному сообщению за раз
channel.basic_consume(queue=ORDER_PROCESSING_QUEUE, on_message_callback=callback)

print("[*] Starting to consume messages...")

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\n[*] Stopping Order Processor Worker...")
    channel.stop_consuming()
    connection.close()
    print("[*] Worker stopped")
