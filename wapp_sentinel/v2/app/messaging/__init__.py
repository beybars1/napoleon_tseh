"""
Message broker abstraction layer.

Provides a unified API for message queue operations.
Switch between RabbitMQ (local) and Azure Service Bus (production)
via the BROKER_TYPE environment variable.

Usage:
    from app.messaging import get_broker, AckAction
    
    # Publishing
    broker = get_broker()
    broker.publish("my_queue", {"key": "value"})
    
    # Consuming
    def handler(message: dict) -> AckAction:
        process(message)
        return AckAction.ACK
    
    broker.consume("my_queue", handler)
"""
import os
import logging

from app.messaging.base import MessageBroker, AckAction

logger = logging.getLogger(__name__)

# Singleton broker instance
_broker_instance: MessageBroker | None = None


def get_broker() -> MessageBroker:
    """
    Factory function that returns a MessageBroker instance based on BROKER_TYPE env var.
    
    BROKER_TYPE=rabbitmq   → RabbitMQBroker (default, for local dev)
    BROKER_TYPE=servicebus → ServiceBusBroker (for Azure production)
    
    Returns a singleton instance (one broker per process).
    """
    global _broker_instance

    if _broker_instance is not None:
        return _broker_instance

    broker_type = os.getenv("BROKER_TYPE", "rabbitmq").lower()

    if broker_type == "rabbitmq":
        from app.messaging.rabbitmq_broker import RabbitMQBroker
        _broker_instance = RabbitMQBroker()
        logger.info("Using RabbitMQ broker")

    elif broker_type == "servicebus":
        from app.messaging.servicebus_broker import ServiceBusBroker
        _broker_instance = ServiceBusBroker()
        logger.info("Using Azure Service Bus broker")

    else:
        raise ValueError(
            f"Unknown BROKER_TYPE: '{broker_type}'. "
            f"Supported values: 'rabbitmq', 'servicebus'"
        )

    return _broker_instance


__all__ = ["get_broker", "MessageBroker", "AckAction"]
