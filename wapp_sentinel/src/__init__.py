"""
WhatsApp Sentinel - A WhatsApp message monitoring and order processing system
"""

from .core.config import settings
from .core.database import get_db, Order
from .services.greenapi_service import GreenAPIService
from .processors.message_processor import MessageProcessor

__version__ = "1.0.0"
