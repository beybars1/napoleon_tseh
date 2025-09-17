from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from ..services.greenapi_service import GreenAPIService
from ..services.openai_service import parse_order, consolidate_orders
from ..core.database import Order, SessionLocal

class MessageProcessor:
    def __init__(self):
        self.greenapi = GreenAPIService()
        self.db = SessionLocal()
        
    def __del__(self):
        self.db.close()
        
    def process_message(self, message: Dict) -> Optional[Order]:
        """Process a single message and return Order if created"""
        try:
            msg_id = message.get('idMessage')
            msg_text = message.get('textMessage', '')
            
            if not msg_id or not msg_text:
                return None
                
            # Check if already processed
            existing = self.db.query(Order).filter(Order.message_id == msg_id).first()
            if existing:
                return None
                
            # Parse with OpenAI
            parsed_data = parse_order(msg_text)
            
            # Create order record
            order = Order(
                message_id=msg_id,
                chat_id=message.get('chatId'),
                sender=message.get('senderData', {}).get('sender', ''),
                raw_message=msg_text,
                parsed_data=json.dumps(parsed_data),
                order_date=parsed_data.get("order_date") if parsed_data.get("is_order") else None,
                customer_name=parsed_data.get("customer_name") if parsed_data.get("is_order") else None,
                total_amount=parsed_data.get("total_amount") if parsed_data.get("is_order") else None,
                delivery_time=parsed_data.get("delivery_time") if parsed_data.get("is_order") else None,
                processed=not parsed_data.get("is_order", False)
            )
            
            self.db.add(order)
            self.db.commit()
            
            return order
            
        except Exception as e:
            print(f"Error processing message: {e}")
            self.db.rollback()
            return None
            
    def process_chat_history(
        self,
        chat_id: str,
        days_back: int = 7,
        message_type: Optional[str] = None
    ) -> Dict:
        """
        Process chat history and return statistics
        
        Args:
            chat_id: Chat ID to process
            days_back: Number of days to look back
            message_type: Optional filter for message type
            
        Returns:
            Processing statistics
        """
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Get messages
        messages = self.greenapi.get_messages_by_date_range(
            chat_id=chat_id,
            start_date=start_date,
            message_type=message_type
        )
        
        stats = {
            "total_messages": len(messages),
            "processed": 0,
            "orders_found": 0,
            "errors": 0
        }
        
        # Process each message
        for msg in messages:
            try:
                order = self.process_message(msg)
                if order:
                    stats["processed"] += 1
                    if order.order_date:  # Is an order
                        stats["orders_found"] += 1
            except Exception as e:
                print(f"Error processing message: {e}")
                stats["errors"] += 1
                continue
                
        return stats
        
    def get_unprocessed_orders(self, date_str: Optional[str] = None) -> List[Order]:
        """Get unprocessed orders for a specific date"""
        query = self.db.query(Order).filter(Order.processed == False)
        
        if date_str:
            query = query.filter(Order.order_date == date_str)
            
        return query.all()
        
    def consolidate_and_send_orders(self, orders: List[Order], target_chat_id: str) -> bool:
        """Consolidate orders and send to target chat"""
        try:
            # Prepare orders data
            orders_data = []
            for order in orders:
                parsed = json.loads(order.parsed_data)
                if parsed.get("is_order"):
                    orders_data.append(parsed)
                    
            if not orders_data:
                return False
                
            # Generate consolidated message
            consolidated_message = consolidate_orders(orders_data, datetime.now().strftime("%Y-%m-%d"))
            
            # Send message
            result = self.greenapi.send_message(target_chat_id, consolidated_message)
            
            if "error" not in result:
                # Mark orders as processed
                for order in orders:
                    order.processed = True
                self.db.commit()
                return True
                
            return False
            
        except Exception as e:
            print(f"Error consolidating orders: {e}")
            return False
