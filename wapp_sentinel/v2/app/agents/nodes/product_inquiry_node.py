"""
Product Inquiry Node - Answers questions about menu, prices, flavors
"""
import re
import os
from openai import OpenAI
from app.agents.state import ConversationState
from app.agents.tools.product_tools import get_all_products, format_product_catalog, format_menu_for_user
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
        
        # Detect language of the CURRENT message to ensure response matches
        def _detect_lang(text: str) -> str:
            kz_chars = set('әіңғүұқөһ')
            kz_words = {'сәлем', 'ертең', 'керек', 'маған', 'жақсы', 'рахмет', 'қанша',
                        'менюді', 'көрсет', 'бар', 'не', 'тапсырыс', 'болады', 'қалай'}
            text_lower = text.lower()
            if any(c in kz_chars for c in text_lower):
                return 'kz'
            if any(w in text_lower.split() for w in kz_words):
                return 'kz'
            return 'ru'
        
        current_lang = _detect_lang(user_message)
        
        # Check if user is asking for the full menu
        menu_patterns = [
            r'\bменю\b', r'\bмәзір\b', r'\bкаталог\b', r'\bпрайс\b',
            r'\bассортимент\b', r'\bсписок\b', r'\bцен[аы]\b', r'\bбағ[а]?\b',
            r'\bчто есть\b', r'\bне бар\b', r'\bпокаж', r'\bкөрсет',
        ]
        is_menu_request = any(re.search(p, user_message.lower()) for p in menu_patterns)
        
        if is_menu_request:
            # Direct menu display — use strict template, no LLM generation
            assistant_message = format_menu_for_user(products, lang=current_lang)
        else:
            # Specific question about products — use LLM
            lang_directive = "ВАЖНО: Текущее сообщение клиента написано на РУССКОМ — отвечай СТРОГО на русском языке!" if current_lang == 'ru' else "МАҢЫЗДЫ: Клиенттің қазіргі хабарламасы ҚАЗАҚ тілінде — ТІКЕЛЕЙ қазақ тілінде жауап бер!"
            
            # Build conversation history for context
            history = []
            for msg in state["messages"][-5:]:
                history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Pre-formatted menu for LLM reference
            menu_ru = format_menu_for_user(products, lang="ru")
            menu_kz = format_menu_for_user(products, lang="kz")
            
            system_prompt = f"""Ты — вежливый помощник Napoleon Tseh, кондитерской по производству авторских тортов Наполеон в Алматы.

Наш каталог:
{catalog}

Правила:
- Минимальный заказ: 1.5 кг
- Минимальное время подготовки: 4 часа
- Только самовывоз (доставки нет)
- Оплата: 100% предоплата или наличные при получении
- Кастомизация (особый декор, надписи) → переключай на оператора

ПРАВИЛА ОБЩЕНИЯ:
- Обращайся к клиенту на «Вы» (вежливая форма)
- Отвечай на том языке, на котором написал клиент

ВАЖНО — ОТОБРАЖЕНИЕ МЕНЮ:
Если клиент просит показать меню/прайс/каталог, выведи его РОВНО в таком формате (на языке клиента):

Русский:
{menu_ru}

Казахский:
{menu_kz}

НЕ меняй формат меню, не добавляй лишние описания к каждому торту, НЕ переформатируй.

Если клиент задаёт конкретный вопрос (состав, вкус, аллергены) — ответь кратко и по делу.

{lang_directive}"""

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
