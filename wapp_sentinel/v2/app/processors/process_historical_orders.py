"""
Script to process historical messages from target chat_id
This script publishes all unprocessed messages to the order_processing queue
Run this once to process historical data
"""

import pika
import os
import json
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database.database import SessionLocal
from app.database.models import IncomingMessage, OutgoingMessage, OutgoingAPIMessage
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
ORDER_PROCESSING_QUEUE = os.getenv("ORDER_PROCESSING_QUEUE", "order_processing")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID", "")


def publish_to_order_queue(connection, message_data: dict, table_name: str, message_id: int, timestamp, text: str, chat_id: str):
    """Publish message to order processing queue"""
    try:
        channel = connection.channel()
        channel.queue_declare(queue=ORDER_PROCESSING_QUEUE, durable=True)
        
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
        return True
    except Exception as e:
        print(f"[!] Error publishing to order queue: {e}")
        return False


def process_historical_messages():
    """Process all historical messages from target chat_id"""
    
    print(f"[*] Processing historical messages from chat_id: {TARGET_CHAT_ID}")
    print(f"[*] Connecting to RabbitMQ...")
    
    # Подключаемся к RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    
    # Подключаемся к БД
    db = SessionLocal()
    
    total_published = 0
    
    try:
        # 1. Обрабатываем incoming_message
        print(f"\n[1/3] Processing incoming_message table...")
        incoming_messages = db.query(IncomingMessage).filter(
            IncomingMessage.chat_id == TARGET_CHAT_ID,
            IncomingMessage.order_processed == False,
            IncomingMessage.text_message.isnot(None)
        ).all()
        
        print(f"[i] Found {len(incoming_messages)} unprocessed messages")
        
        for msg in incoming_messages:
            if publish_to_order_queue(
                connection=connection,
                message_data=msg.raw_data if hasattr(msg, 'raw_data') else {},
                table_name='incoming_message',
                message_id=msg.id,
                timestamp=msg.timestamp,
                text=msg.text_message,
                chat_id=msg.chat_id
            ):
                total_published += 1
                print(f"[→] Published: incoming_message id={msg.id}")
        
        # 2. Обрабатываем outgoing_message
        print(f"\n[2/3] Processing outgoing_message table...")
        outgoing_messages = db.query(OutgoingMessage).filter(
            OutgoingMessage.chat_id == TARGET_CHAT_ID,
            OutgoingMessage.order_processed == False,
            OutgoingMessage.text.isnot(None)
        ).all()
        
        print(f"[i] Found {len(outgoing_messages)} unprocessed messages")
        
        for msg in outgoing_messages:
            if publish_to_order_queue(
                connection=connection,
                message_data=msg.raw_data if hasattr(msg, 'raw_data') else {},
                table_name='outgoing_message',
                message_id=msg.id,
                timestamp=msg.timestamp,
                text=msg.text,
                chat_id=msg.chat_id
            ):
                total_published += 1
                print(f"[→] Published: outgoing_message id={msg.id}")
        
        # 3. Обрабатываем outgoing_api_message
        print(f"\n[3/3] Processing outgoing_api_message table...")
        outgoing_api_messages = db.query(OutgoingAPIMessage).filter(
            OutgoingAPIMessage.chat_id == TARGET_CHAT_ID,
            OutgoingAPIMessage.order_processed == False,
            OutgoingAPIMessage.text.isnot(None)
        ).all()
        
        print(f"[i] Found {len(outgoing_api_messages)} unprocessed messages")
        
        for msg in outgoing_api_messages:
            if publish_to_order_queue(
                connection=connection,
                message_data=msg.raw_data if hasattr(msg, 'raw_data') else {},
                table_name='outgoing_api_message',
                message_id=msg.id,
                timestamp=msg.timestamp,
                text=msg.text,
                chat_id=msg.chat_id
            ):
                total_published += 1
                print(f"[→] Published: outgoing_api_message id={msg.id}")
        
        print(f"\n[✓] Successfully published {total_published} messages to order_processing queue")
        print(f"[i] These messages will be processed by order_processor_worker")
        
    except Exception as e:
        print(f"\n[!] Error: {e}")
        return False
    finally:
        db.close()
        connection.close()
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Historical Order Messages Processor")
    print("=" * 60)
    
    confirm = input(f"\nThis will publish all unprocessed messages from chat_id '{TARGET_CHAT_ID}' to the order processing queue.\n\nContinue? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        print("\n[*] Starting processing...")
        if process_historical_messages():
            print("\n[✓] Done! Historical messages are now in the queue.")
            print("[i] Make sure order_processor_worker.py is running to process them.")
        else:
            print("\n[!] Processing failed!")
    else:
        print("\n[i] Cancelled by user")
