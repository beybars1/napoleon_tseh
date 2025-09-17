"""Core application components"""

from .config import settings
from .database import get_db, Order
from .main import app
