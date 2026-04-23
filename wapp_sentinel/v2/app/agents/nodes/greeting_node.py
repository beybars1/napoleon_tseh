"""
Greeting Node - Handles initial greetings and welcomes
"""
import os
from openai import OpenAI
from app.agents.state import ConversationState

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def greeting_node(state: ConversationState) -> ConversationState:
    """
    Handle greeting intent
    - Smart personalized greeting
    - Brief brand introduction (no full menu)
    - Set stage to 'inquiry'
    """
    
    user_message = state["messages"][-1]["content"] if state["messages"] else ""

    system_prompt = """Ты — вежливый помощник кондитерской Napoleon Tseh в Алматы.

О НАС:
- Мы изготавливаем авторские торты Наполеон разных видов на заказ
- Акцент на качество и натуральные ингредиенты
- Также есть десертные наборы (мини-наполеоны)
- Всё готовится свежим под каждый заказ

ЗАДАЧА: Поприветствовать клиента и кратко представиться. НЕ показывай полное меню с ценами — просто расскажи кто мы и что делаем. Предложи рассказать подробнее о тортах или помочь с заказом.

ПРАВИЛА ОБЩЕНИЯ:
- Обращайся к клиенту на «Вы» (вежливая форма)
- Отвечай на том языке, на котором написал клиент (русский или казахский, или смешанно)
- Если клиент пишет на казахском — отвечай на казахском
- Если на русском — на русском
- Если смешанно — можно смешанно
- Будь тёплым, профессиональным, но кратким (3-5 строк максимум)
- Используй 1-2 эмодзи, не перегружай"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message or "Привет"}
        ],
        temperature=0.7,
        max_tokens=200
    )

    greeting_message = response.choices[0].message.content.strip()
    
    state["messages"].append({
        "role": "assistant",
        "content": greeting_message,
        "timestamp": state["updated_at"]
    })
    
    state["conversation_stage"] = "inquiry"
    state["next_step"] = "router"
    
    return state
