from openai_service import parse_order
import json

# Test with one of your real messages
test_message = """Заказ на завтра 15.05
Наполеон 1 кг
Время : 16:00
Бекет 
+7 747 755 3508
Оплачено ✅"""

print("Testing OpenAI parsing...")
print(f"Input message: {test_message}")
print("\n" + "="*50)

try:
    result = parse_order(test_message)
    print("OpenAI Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
    print("Check your OpenAI API key in .env file")