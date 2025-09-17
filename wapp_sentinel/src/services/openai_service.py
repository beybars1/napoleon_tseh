import openai
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Simple client initialization
def get_openai_client():
    return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ORDER_PARSING_PROMPT = """
You are a pastry order parser for a Russian bakery. Extract order information from WhatsApp messages.

IMPORTANT: 
- Current year is 2025
- If date says "завтра" (tomorrow), calculate tomorrow's date from current date
- If date format is "DD.MM", assume year 2025
- If order says "на завтра" or "на сегодня", use appropriate date
- Customer names are usually single names in Russian (like Бекет, Гульмира, Ирина, Шолпан)

Return ONLY valid JSON in this format:
{
  "is_order": true/false,
  "order_date": "YYYY-MM-DD",
  "customer_name": "string",
  "items": [
    {"product": "string", "quantity": "string", "notes": "string"}
  ],
  "total_amount": null or number,
  "delivery_time": "string or null",
  "notes": "additional notes"
}

If the message is not an order, return {"is_order": false}.
Extract all pastry items mentioned (Наполеон, торт, etc).

Message to parse:
"""

CONSOLIDATION_PROMPT = """
You are formatting daily pastry orders for an operational team.

Create a clear, structured WhatsApp message for today's orders.
Format should be:

🍰 *DAILY ORDERS - {date}*

*Customer Name*
- Product x Quantity (notes if any)
- Total: $X.XX
- Delivery: Time

Separate each customer with a line break.
At the end add: *Total Orders: X*

Orders data:
"""

def parse_order(message_text: str):
    """Parse WhatsApp message to extract order information"""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": ORDER_PARSING_PROMPT},
                {"role": "user", "content": message_text}
            ],
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        return json.loads(result)
    except Exception as e:
        print(f"Error parsing order: {e}")
        return {"is_order": False, "error": str(e)}

def consolidate_orders(orders_data: list, date_str: str):
    """Generate consolidated daily orders message"""
    try:
        client = get_openai_client()
        orders_json = json.dumps(orders_data, indent=2)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": CONSOLIDATION_PROMPT},
                {"role": "user", "content": f"Date: {date_str}\n\nOrders:\n{orders_json}"}
            ],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error consolidating orders: {e}")
        return f"Error generating daily orders summary: {str(e)}"