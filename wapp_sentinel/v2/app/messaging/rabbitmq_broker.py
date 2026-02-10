"""
RabbitMQ implementation of MessageBroker.

Used for local development with docker-compose.
"""
import os
import json
import logging
import pika
from typing import Callable

from app.messaging.base import MessageBroker, AckAction

logger = logging.getLogger(__name__)


class RabbitMQBroker(MessageBroker):
    """
    RabbitMQ broker using pika library.
    
    Environment variables:
        RABBITMQ_HOST: RabbitMQ hostname (default: localhost)
        RABBITMQ_PORT: AMQP port (default: 5672)
        RABBITMQ_USER: Username (default: guest)
        RABBITMQ_PASSWORD: Password (default: guest)
    """

    def __init__(self):
        self._host = os.getenv("RABBITMQ_HOST", "localhost")
        self._port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self._user = os.getenv("RABBITMQ_USER", "guest")
        self._password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None

    def _get_connection(self) -> pika.BlockingConnection:
        """Get or create a RabbitMQ connection."""
        if self._connection is None or self._connection.is_closed:
            credentials = pika.PlainCredentials(self._user, self._password)
            parameters = pika.ConnectionParameters(
                host=self._host,
                port=self._port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self._connection = pika.BlockingConnection(parameters)
            self._channel = None  # Reset channel on new connection
            logger.info(f"Connected to RabbitMQ at {self._host}:{self._port}")
        return self._connection

    def _get_channel(self) -> pika.adapters.blocking_connection.BlockingChannel:
        """Get or create a channel."""
        conn = self._get_connection()
        if self._channel is None or self._channel.is_closed:
            self._channel = conn.channel()
        return self._channel

    def publish(self, queue: str, message: dict) -> bool:
        """Publish a message to a RabbitMQ queue."""
        try:
            channel = self._get_channel()
            channel.queue_declare(queue=queue, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),  # persistent
            )
            logger.debug(f"Published to queue '{queue}'")
            return True
        except Exception as e:
            logger.error(f"Error publishing to RabbitMQ queue '{queue}': {e}")
            # Reset connection on error so next call reconnects
            self._connection = None
            self._channel = None
            return False

    def consume(self, queue: str, callback: Callable[[dict], AckAction], prefetch: int = 1) -> None:
        """Start blocking consumption from a RabbitMQ queue."""
        channel = self._get_channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_qos(prefetch_count=prefetch)

        def _on_message(ch, method, properties, body):
            try:
                message = json.loads(body)
                action = callback(message)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from queue '{queue}': {e}")
                action = AckAction.NACK
            except Exception as e:
                logger.error(f"Unhandled error in consumer callback for queue '{queue}': {e}", exc_info=True)
                action = AckAction.REQUEUE

            if action == AckAction.ACK:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            elif action == AckAction.NACK:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            elif action == AckAction.REQUEUE:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        channel.basic_consume(queue=queue, on_message_callback=_on_message)
        logger.info(f"Consuming from queue '{queue}'. Press CTRL+C to exit.")

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            channel.stop_consuming()

    def close(self) -> None:
        """Close the RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            logger.info("RabbitMQ connection closed")
        self._connection = None
        self._channel = None
