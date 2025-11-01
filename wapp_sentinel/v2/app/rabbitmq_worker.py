import pika
import os
import ast
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from app.main import save_event_to_db
from app.database.database import SessionLocal

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "greenapi_notifications")

connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

print(f"[*] Waiting for messages in queue '{RABBITMQ_QUEUE}'. To exit press CTRL+C")

def callback(ch, method, properties, body):
    print(f"[x] Received message: {body}")
    try:
        # Преобразуем строку обратно в dict
        notification_data = ast.literal_eval(body.decode())
        save_event_to_db(notification_data)
        print("[+] Saved to DB")
    except Exception as e:
        print(f"[!] Error processing message: {e}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)

channel.start_consuming()
