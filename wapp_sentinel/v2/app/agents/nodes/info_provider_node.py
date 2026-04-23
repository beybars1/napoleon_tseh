"""
Info Provider Node - Answers delivery, payment, and general policy questions
"""
import os
from openai import OpenAI
from app.agents.state import ConversationState

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def info_provider_node(state: ConversationState) -> ConversationState:
    """
    Handle delivery_inquiry and payment_inquiry intents
    - Provide policy information
    - Escalate if delivery requested (pickup only)
    """
    
    user_message = state["messages"][-1]["content"]
    last_intent = state.get("last_intent", "")
    
    # Detect language of the CURRENT message
    def _detect_lang(text: str) -> str:
        kz_chars = set('әіңғүұқөһ')
        kz_words = {'жеткізу', 'төлем', 'қалай', 'бар', 'жоқ', 'маған', 'қайда'}
        text_lower = text.lower()
        if any(c in kz_chars for c in text_lower):
            return 'kz'
        if any(w in text_lower.split() for w in kz_words):
            return 'kz'
        return 'ru'
    
    current_lang = _detect_lang(user_message)
    lang_directive = "ВАЖНО: Текущее сообщение клиента на РУССКОМ — отвечай СТРОГО на русском!" if current_lang == 'ru' else "МАҢЫЗДЫ: Клиенттің хабарламасы ҚАЗАҚША — қазақ тілінде жауап бер!"
    
    # Check if delivery is requested
    if last_intent == "delivery_inquiry":
        delivery_keywords = ["доставка", "доставить", "привезите", "курьер"]
        if any(kw in user_message.lower() for kw in delivery_keywords):
            # Escalate for delivery requests
            state["escalation_reason"] = "Запрос на доставку (только самовывоз)"
            state["flagged_for_human"] = True
            state["next_step"] = "escalate"
            return state
    
    # Generate informational response
    system_prompt = """Ты — вежливый помощник Napoleon Tseh. Отвечай на вопросы о доставке и оплате.

Политики:
- Доставка: НЕТ. Только самовывоз по адресу (уточняет менеджер)
- Оплата: 100% предоплата переводом ИЛИ наличные при получении
- Минимальное время подготовки: 4 часа
- Контакты: через WhatsApp или телефон менеджера

ПРАВИЛА ОБЩЕНИЯ:
- Обращайся на «Вы» (вежливая форма)
- Отвечай на том языке, на котором написал клиент (русский / казахский / смешанно)

Если клиент настаивает на доставке, вежливо объясните что мы работаем только на самовывоз, но можно переключить на менеджера для особых случаев.

{lang_directive}"""

    history = []
    for msg in state["messages"][-5:]:
        history.append({"role": msg["role"], "content": msg["content"]})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            *history
        ],
        temperature=0.7,
        max_tokens=200
    )
    
    assistant_message = response.choices[0].message.content.strip()
    
    state["messages"].append({
        "role": "assistant",
        "content": assistant_message,
        "timestamp": state["updated_at"]
    })
    
    state["next_step"] = "router"
    
    return state
