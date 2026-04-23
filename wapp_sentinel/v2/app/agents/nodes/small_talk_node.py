"""
Small Talk Node - Handles off-topic conversation politely
"""
import os
from openai import OpenAI
from app.agents.state import ConversationState

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def small_talk_node(state: ConversationState) -> ConversationState:
    """
    Handle small_talk intent
    - Brief friendly response
    - Gently redirect to business
    """
    
    user_message = state["messages"][-1]["content"]
    
    # Detect language of current message
    def _detect_lang(text: str) -> str:
        kz_chars = set('әіңғүұқөһ')
        text_lower = text.lower()
        if any(c in kz_chars for c in text_lower):
            return 'kz'
        return 'ru'
    
    current_lang = _detect_lang(user_message)
    
    # Check if question is about the business itself (not just chitchat)
    import re
    business_patterns = [
        r"\bкто\s+ты\b", r"\bпредставься\b", r"\bкто\s+вы\b",
        r"\bменю\b", r"\bприветствие\b", r"\bстатичное\b"
    ]
    is_business_question = any(re.search(pattern, user_message.lower()) for pattern in business_patterns)
    
    if is_business_question:
        # Redirect to full greeting with menu
        from app.agents.nodes.greeting_node import greeting_node
        return greeting_node(state)
    
    lang_directive = "ВАЖНО: Текущее сообщение клиента на РУССКОМ — отвечай СТРОГО на русском!" if current_lang == 'ru' else "МАҢЫЗДЫ: Клиенттің хабарламасы ҚАЗАҚША — қазақ тілінде жауап бер!"
    
    system_prompt = f"""Ты — вежливый помощник Napoleon Tseh. Клиент говорит не по делу (погода, комплименты, шутки).

ПРАВИЛА ОБЩЕНИЯ:
- Обращайся на «Вы» (вежливая форма)
- Отвечай на том языке, на котором написал клиент (русский / казахский / смешанно)
- Ответь вежливо и кратко (1-2 предложения), затем мягко верни к теме тортов

Пример (РУ):
Клиент: "Какая сегодня погода?"
Ты: "Не знаю точно, но надеюсь хорошая! 😊 Кстати, не хотите ли заказать торт Наполеон?"

Пример (КЗ):
Клиент: "Бүгін ауа-райы қалай?"
Ты: "Анық білмеймін, бірақ жақсы болса екен деп тілеймін! 😊 Айтпақшы, Наполеон тортын тапсырыс бергіңіз келе ме?"

Будь дружелюбным, но деловым.

{lang_directive}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.8,
        max_tokens=100
    )
    
    assistant_message = response.choices[0].message.content.strip()
    
    state["messages"].append({
        "role": "assistant",
        "content": assistant_message,
        "timestamp": state["updated_at"]
    })
    
    state["next_step"] = "router"
    
    return state
