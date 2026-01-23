"""
Greeting Node - Handles initial greetings and welcomes
"""
from app.agents.state import ConversationState


def greeting_node(state: ConversationState) -> ConversationState:
    """
    Handle greeting intent
    - Welcome message
    - Brief menu overview
    - Set stage to 'inquiry'
    """
    
    greeting_message = """Добрый день! 👋

Мы — Napoleon Tseh, изготавливаем авторские торты Наполеон на заказ в Алматы.

🍰 Наше меню:
• Классический Наполеон — 8000₸/кг
• Шоколадный — 9000₸/кг
• Клубничный — 9500₸/кг
• Кофейный, Карамельный, Малиновый — 9000₸/кг
• Фисташковый, Ванильный — 10000₸/кг
• Десертные наборы — от 4500₸

⏱ Минимальное время подготовки: 4 часа
📍 Самовывоз (адрес уточню при оформлении)

Чем могу помочь? Хотите узнать подробнее о тортах или оформить заказ?"""
    
    state["messages"].append({
        "role": "assistant",
        "content": greeting_message,
        "timestamp": state["updated_at"]
    })
    
    state["conversation_stage"] = "inquiry"
    state["next_step"] = "router"
    
    return state
