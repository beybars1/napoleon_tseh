"""
Azure Service Bus implementation of MessageBroker.

Used in Azure production deployment (Container Apps).
"""
import os
import json
import logging
import time
from typing import Callable

from app.messaging.base import MessageBroker, AckAction

logger = logging.getLogger(__name__)

try:
    from azure.servicebus import ServiceBusClient, ServiceBusMessage, ServiceBusSender, ServiceBusReceiver
    HAS_SERVICEBUS = True
except ImportError:
    HAS_SERVICEBUS = False


class ServiceBusBroker(MessageBroker):
    """
    Azure Service Bus broker.
    
    Environment variables:
        SERVICE_BUS_CONNECTION_STRING: Full connection string from Azure portal
    
    Queues must be pre-created in Azure (via CLI or portal).
    """

    def __init__(self):
        if not HAS_SERVICEBUS:
            raise ImportError(
                "azure-servicebus package is not installed. "
                "Install it with: pip install azure-servicebus"
            )

        connection_string = os.getenv("SERVICE_BUS_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("SERVICE_BUS_CONNECTION_STRING environment variable is required")

        self._client = ServiceBusClient.from_connection_string(connection_string)
        self._senders: dict[str, ServiceBusSender] = {}
        logger.info("Connected to Azure Service Bus")

    def _get_sender(self, queue: str) -> ServiceBusSender:
        """Get or create a sender for a queue."""
        if queue not in self._senders:
            self._senders[queue] = self._client.get_queue_sender(queue_name=queue)
        return self._senders[queue]

    def publish(self, queue: str, message: dict) -> bool:
        """Publish a message to an Azure Service Bus queue."""
        try:
            sender = self._get_sender(queue)
            sb_message = ServiceBusMessage(json.dumps(message))
            sender.send_messages(sb_message)
            logger.debug(f"Published to Service Bus queue '{queue}'")
            return True
        except Exception as e:
            logger.error(f"Error publishing to Service Bus queue '{queue}': {e}")
            return False

    def consume(self, queue: str, callback: Callable[[dict], AckAction], prefetch: int = 1) -> None:
        """
        Start consuming messages from an Azure Service Bus queue (blocking).
        
        Uses long-polling with receive_messages() in an infinite loop.
        """
        logger.info(f"Consuming from Service Bus queue '{queue}'. Press CTRL+C to exit.")

        try:
            with self._client.get_queue_receiver(
                queue_name=queue,
                prefetch_count=prefetch,
            ) as receiver:
                while True:
                    # Long-poll: wait up to 30 seconds for messages
                    messages = receiver.receive_messages(
                        max_message_count=1,
                        max_wait_time=30,
                    )

                    for msg in messages:
                        try:
                            body = str(msg)
                            message = json.loads(body)
                            action = callback(message)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from Service Bus queue '{queue}': {e}")
                            action = AckAction.NACK
                        except Exception as e:
                            logger.error(f"Unhandled error in consumer callback for queue '{queue}': {e}", exc_info=True)
                            action = AckAction.REQUEUE

                        if action == AckAction.ACK:
                            receiver.complete_message(msg)
                        elif action == AckAction.NACK:
                            receiver.dead_letter_message(msg, reason="Processing failed")
                        elif action == AckAction.REQUEUE:
                            receiver.abandon_message(msg)

        except KeyboardInterrupt:
            logger.info("Stopping Service Bus consumer...")

    def close(self) -> None:
        """Close all senders and the Service Bus client."""
        for sender in self._senders.values():
            try:
                sender.close()
            except Exception:
                pass
        self._senders.clear()

        try:
            self._client.close()
        except Exception:
            pass
        logger.info("Service Bus connection closed")
