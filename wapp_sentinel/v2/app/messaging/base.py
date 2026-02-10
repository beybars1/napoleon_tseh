"""
Abstract Message Broker interface.

Provides a unified API for message queue operations,
allowing transparent switching between RabbitMQ (local dev) and Azure Service Bus (production).
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


class AckAction(Enum):
    """Action to take after processing a message."""
    ACK = "ack"           # Message processed successfully, remove from queue
    NACK = "nack"         # Message failed, do NOT requeue (dead-letter)
    REQUEUE = "requeue"   # Message failed, put back in queue for retry


class MessageBroker(ABC):
    """
    Abstract base class for message broker implementations.
    
    Usage:
        # Publishing
        broker = get_broker()
        broker.publish("my_queue", {"key": "value"})
        
        # Consuming
        def handler(message: dict) -> AckAction:
            process(message)
            return AckAction.ACK
        
        broker.consume("my_queue", handler)
    """

    @abstractmethod
    def publish(self, queue: str, message: dict) -> bool:
        """
        Publish a message to a queue.
        
        Args:
            queue: Queue name
            message: Dict payload (will be JSON-serialized)
            
        Returns:
            True if published successfully, False otherwise
        """
        pass

    @abstractmethod
    def consume(self, queue: str, callback: Callable[[dict], AckAction], prefetch: int = 1) -> None:
        """
        Start consuming messages from a queue (blocking).
        
        Args:
            queue: Queue name
            callback: Function that receives a dict and returns AckAction
            prefetch: Number of unacknowledged messages to prefetch
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close all connections and clean up resources."""
        pass
