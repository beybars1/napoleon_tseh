"""
Intent Classifier - Classifies user messages into intent categories
"""
import os
from openai import OpenAI
from typing import Literal

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

IntentType = Literal[
    "greeting",
    "product_inquiry",
    "order_placement",
    "order_info_provision",
    "order_reset",  # Cancel/restart order completely
    "order_modification",  # Change specific part of order (not full reset)
    "acknowledgment",  # "хорошо", "ок", "понятно" after error/correction
    "customization_request",
    "delivery_inquiry",
    "payment_inquiry",
    "order_status",
    "complaint",
    "small_talk"
]


def classify_intent(message: str, conversation_history: list[dict]) -> dict:
    """
    Classify user message intent using GPT-4o-mini
    
    Args:
        message: Current user message
        conversation_history: Recent conversation context
    
    Returns:
        {"intent": IntentType, "confidence": float}
    """
    
    context = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in conversation_history[-5:]
    ])
    
    prompt = f"""Analyze this customer message in a Napoleon cake ordering conversation.

Recent context:
{context}

Current message: {message}

Classify into ONE intent:
- greeting: Hi, hello, good day, привет, здравствуйте
- product_inquiry: Questions about MENU, prices, flavors, sizes, "покажи меню", "что есть", "какие торты"
- order_placement: Wants to order, place order, buy cake, "хочу заказать"
- order_info_provision: Providing order details (date, time, name, phone, quantity, payment method)
- order_reset: FULL cancellation/restart ONLY: "сброс", "заново", "отмена заказа", "начать сначала", "удалить заказ"
- order_modification: Change SPECIFIC part of existing order: "другое время", "поменять дату", "изменить"
- acknowledgment: Simple acknowledgment WITHOUT new info: "хорошо", "ок", "понятно", "спасибо"
- customization_request: Special decorations, custom text, unique modifications
- delivery_inquiry: Asking about delivery, shipping, location
- payment_inquiry: Payment methods questions (NOT providing payment choice)
- order_status: Checking existing order: "мой заказ", "статус заказа", "что я заказал", "расскажи о заказе"
- complaint: Issues, problems, dissatisfaction
- small_talk: Off-topic chat, weather, compliments

CRITICAL RULES:
1. "покажи меню" / "что есть" / "какие торты" = ALWAYS product_inquiry (never order_reset!)
2. "заново" / "сброс" / "отмена" = order_reset ONLY if about the ORDER
3. "мой заказ" / "что я заказал" / "расскажи о заказе" = order_status
4. Date/time/name/phone in message = order_info_provision
5. IGNORE previous context when classifying "покажи меню" - it's ALWAYS product_inquiry

Respond ONLY with JSON: {{"intent": "...", "confidence": 0.0-1.0}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an intent classifier for a cake ordering chatbot. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        import json
        result = json.loads(response.choices[0].message.content.strip())
        return result
        
    except Exception as e:
        # Fallback to product_inquiry for safety
        return {"intent": "product_inquiry", "confidence": 0.5}
