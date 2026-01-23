"""
Product Inquiry Node - Answers questions about menu, prices, flavors
"""
import os
from openai import OpenAI
from app.agents.state import ConversationState
from app.agents.tools.product_tools import get_all_products, format_product_catalog
from app.database.database import SessionLocal

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def product_inquiry_node(state: ConversationState) -> ConversationState:
    """
    Handle product inquiry intent
    - Query product database
    - Generate contextual answer using GPT-4o-mini
    - Maintain conversation flow
    """
    
    db = SessionLocal()
    try:
        # Get product catalog
        products = get_all_products(db)
        catalog = format_product_catalog(products)
        
        # Get user's last message
        user_message = state["messages"][-1]["content"]
        
        # Build conversation history for context
        history = []
        for msg in state["messages"][-5:]:
            history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Generate response using GPT-4o-mini
        system_prompt = f"""Ты — помощник Napoleon Tseh, кондитерской по производству авторских тортов Наполеон в Алматы.

Наш каталог:
{catalog}

Правила:
- Минимальный заказ: 1.5 кг
- Минимальное время подготовки: 4 часа
- Только самовывоз (доставки нет)
- Оплата: 100% предоплата или наличные при получении
- Кастомизация (особый декор, надписи) → переключай на оператора

ФОРМАТИРОВАНИЕ ОТВЕТОВ:
- Используй эмодзи для визуальной привлекательности (🍰 🍫 🍓 ☕ 🍬 🫐 🥜 🍦)
- Цены без копеек (8000₸, не 8000.00₸)
- При показе меню группируй: сначала торты, потом наборы
- Описания кратко в 1 строку
- В конце всегда спрашивай что заинтересовало

ПРИМЕР ХОРОШЕГО ОТВЕТА на "какие есть торты":
🍰 Наши торты Наполеон:

• 🥧 Классический — 8000₸/кг
• 🍫 Шоколадный — 9000₸/кг
• 🍓 Клубничный — 9500₸/кг
• ☕ Кофейный — 9000₸/кг
• 🍬 Карамельный — 9000₸/кг
• 🫐 Малиновый — 9500₸/кг
• 🥜 Фисташковый — 10000₸/кг
• 🍦 Ванильный — 8500₸/кг

Минимум 1.5 кг. Какой вас заинтересовал?"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *history
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        assistant_message = response.choices[0].message.content.strip()
        
        state["messages"].append({
            "role": "assistant",
            "content": assistant_message,
            "timestamp": state["updated_at"]
        })
        
        state["conversation_stage"] = "inquiry"
        state["next_step"] = "router"
        
    finally:
        db.close()
    
    return state
