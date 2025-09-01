from database import get_db, Order
from openai_service import consolidate_orders
import json
from datetime import date

def test_daily_consolidation():
    """Test the daily consolidation with existing orders"""
    db = next(get_db())
    
    try:
        # Get all orders from database
        orders = db.query(Order).all()
        print(f"Found {len(orders)} orders in database")
        
        if not orders:
            print("No orders to consolidate")
            return
        
        # Show what we have
        for order in orders:
            parsed = json.loads(order.parsed_data)
            print(f"- {order.customer_name}: {order.order_date} at {order.delivery_time}")
        
        # Test consolidation for today's orders (simulate)
        orders_data = []
        for order in orders:
            parsed = json.loads(order.parsed_data)
            if parsed.get("is_order"):
                orders_data.append(parsed)
        
        if orders_data:
            print(f"\n=== TESTING CONSOLIDATION ===")
            print(f"Consolidating {len(orders_data)} orders...")
            
            # Generate consolidated message
            consolidated_message = consolidate_orders(orders_data, "2023-05-15")
            
            print("\n=== CONSOLIDATED MESSAGE ===")
            print(consolidated_message)
            print("\n" + "="*50)
            
            # This is what would be sent to your operational group
            print("✅ This message would be sent to your operational WhatsApp group!")
        else:
            print("No valid orders to consolidate")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_daily_consolidation()