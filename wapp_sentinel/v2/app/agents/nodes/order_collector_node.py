"""
Order Collector Node - Collects order details through conversation
"""
import os
import re
import logging
from openai import OpenAI
from datetime import datetime
from langgraph.graph import END
from app.agents.state import ConversationState
from app.agents.tools.product_tools import get_product_by_id, search_products, calculate_price, get_all_products, format_product_catalog, format_menu_for_user
from app.agents.tools.order_tools import (
    validate_pickup_date,
    validate_phone,
    check_order_completeness,
    validate_product_availability,
    validate_item_weight,
    validate_order_size,
    resolve_natural_date
)
from app.database.database import SessionLocal

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)


def order_collector_node(state: ConversationState) -> ConversationState:
    """
    Handle order placement and info provision intents
    - Extract structured data from user message
    - Update order_draft
    - Guide user through missing fields
    - Progress to confirmation when complete
    """
    
    db = SessionLocal()
    try:
        user_message = state["messages"][-1]["content"]
        order_draft = state.get("order_draft", {
            "items": [],
            "completeness": {"items": False, "pickup": False, "customer": False, "payment": False}
        })

        logger.info(f"[ORDER_COLLECTOR] INITIAL order_draft: {order_draft}")
        
        # If already in confirming stage, don't process (should go to confirmation_node)
        if state.get("conversation_stage") == "confirming":
            state["messages"].append({
                "role": "assistant",
                "content": "⚠️ Ваш заказ уже сформирован. Пожалуйста, подтвердите его или сообщите, что хотите изменить.",
                "timestamp": state["updated_at"]
            })
            state["next_step"] = END
            db.close()
            return state
        
        # Extract order details using GPT-4o-mini
        pending_product = order_draft.get("pending_product")

        context_note = ""
        if pending_product:
            context_note = f"\nКОНТЕКСТ: Клиент ранее спросил про '{pending_product['name']}', но не указал вес."

        # Get recent conversation history for context (last 3 user messages)
        recent_messages = [m for m in state["messages"] if m["role"] == "user"][-4:-1]  # Exclude current message
        history_context = ""
        if recent_messages:
            history_lines = [f"- {m['content']}" for m in recent_messages]
            history_context = f"\nПРЕДЫДУЩИЕ СООБЩЕНИЯ КЛИЕНТА:\n" + "\n".join(history_lines)

        # Get product catalog for accurate matching
        all_products = get_all_products(db)
        product_catalog = format_product_catalog(all_products)

        extraction_prompt = f"""Извлеки информацию из сообщения клиента. НЕ ПРИДУМЫВАЙ данные!
Клиент может писать на русском, казахском или смешанно.

ТЕКУЩЕЕ СООБЩЕНИЕ: "{user_message}"
{history_context}
{context_note}

КАТАЛОГ ТОВАРОВ:
{product_catalog}

ТЕКУЩИЙ ЗАКАЗ (что уже есть):
{order_draft}

Формат ответа (JSON):
{{
  "products": [{{"name": "название из каталога", "quantity_kg": null, "quantity_sets": null}}],
  "pickup_date": null,
  "pickup_time": null,
  "customer_name": null,
  "customer_phone": null,
  "payment_method": null,
  "special_requests": null
}}

КРИТИЧЕСКИ ВАЖНО:
- Если данных НЕТ в сообщении → null
- НЕ придумывай данные!
- Если клиент пишет "выше написал", "уже писал", "смотри выше", "жоғарыда жаздым" → ищи данные в ПРЕДЫДУЩИХ СООБЩЕНИЯХ
- Телефон может быть в формате: 87001234567, +77001234567, 7 700 123 4567

РАСПОЗНАВАНИЕ ИМЕНИ И ТЕЛЕФОНА:
- "Бибарыс 87006458263" → имя: Бибарыс, телефон: 87006458263
- "Алия +77051234567" → имя: Алия, телефон: +77051234567
- Имя обычно перед номером телефона
- Телефон: 10-11 цифр, начинается с 8 или +7 или 7

ДАТА И ВРЕМЯ — ВАЖНО:
- Сохраняй дату КАК ЕСТЬ из сообщения (включая естественный язык)
- "завтра" → pickup_date = "завтра"
- "ертең" → pickup_date = "ертең"
- "следующий понедельник" → pickup_date = "следующий понедельник"
- "следующая суббота" → pickup_date = "следующая суббота"
- "келесі дүйсенбі" → pickup_date = "келесі дүйсенбі"
- "послезавтра" → pickup_date = "послезавтра"
- "25.01.2026" → pickup_date = "25.01.2026"
- "25 января" → pickup_date = "25 января"
- Дата будет интерпретирована отдельным модулем!

ВРЕМЯ — ПРИНИМАЙ ЛЮБОЕ УКАЗАНИЕ:
- "15:00" → pickup_time = "15:00"
- "на вечер" → pickup_time = "вечер"
- "утром" → pickup_time = "утро"
- "после обеда" → pickup_time = "после обеда"
- "кешке" (казахский: вечером) → pickup_time = "кешке"
- "таңертең" (утром) → pickup_time = "таңертең"
- "часам к 5" → pickup_time = "17:00"
- НЕ оставляй pickup_time = null если клиент указал хоть что-то про время!

ПРАВИЛА:
1. products = [] если товаров нет
2. ТОРТЫ: quantity_kg = вес, quantity_sets = null
3. НАБОРЫ МИНИ: quantity_kg = null, quantity_sets = 1
4. Используй ТОЧНОЕ название из каталога!

ПРИМЕРЫ:
Сообщение: "ертең сағат 14:00-де алып кетемін, Бибарыс 87006458263, алдын ала төлеймін"
Ответ: {{"products": [], "pickup_date": "ертең", "pickup_time": "14:00", "customer_name": "Бибарыс", "customer_phone": "87006458263", "payment_method": "предоплата", "special_requests": null}}

Сообщение: "25.01.2026, 22 00\\nБибарыс 87006458263\\nПредоплата"
Ответ: {{"products": [], "pickup_date": "25.01.2026", "pickup_time": "22:00", "customer_name": "Бибарыс", "customer_phone": "87006458263", "payment_method": "предоплата", "special_requests": null}}

Сообщение: "Наполеон клубничный 3 кг и мини классический"
Ответ: {{"products": [{{"name": "Торт Наполеон Клубничный", "quantity_kg": 3, "quantity_sets": null}}, {{"name": "Набор мини-Наполеонов Классический", "quantity_kg": null, "quantity_sets": 1}}], "pickup_date": null, "pickup_time": null, "customer_name": null, "customer_phone": null, "payment_method": null, "special_requests": null}}

Отвечай ТОЛЬКО валидным JSON."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — экстрактор данных из сообщений клиента. Извлекай ТОЛЬКО явно указанные данные. Отвечай валидным JSON."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.0,  # More deterministic
            max_tokens=400
        )
        
        import json

        try:
            extracted = json.loads(response.choices[0].message.content.strip())
            logger.info(f"[ORDER_COLLECTOR] Extracted from '{user_message}': {extracted}")
        except json.JSONDecodeError as e:
            logger.error(f"[ORDER_COLLECTOR] JSON decode error: {e}, Response: {response.choices[0].message.content}")
            # Fallback if GPT didn't return JSON
            extracted = {}
        
        # Detect client language early so all responses match
        def detect_language(text: str) -> str:
            """Quick detection: 'kz' if Kazakh chars/words present, else 'ru'"""
            kz_chars = set('әіңғүұқөһ')
            kz_words = {'сәлем', 'ертең', 'керек', 'бергім', 'келеді', 'маған', 'жақсы',
                        'рахмет', 'қанша', 'келесі', 'тапсырыс', 'кешке', 'таңертең',
                        'мен', 'болады', 'қалай', 'бар', 'жоқ', 'бүгін', 'сенбі', 'осы'}
            text_lower = text.lower()
            if any(c in kz_chars for c in text_lower):
                return 'kz'
            if any(w in text_lower.split() for w in kz_words):
                return 'kz'
            return 'ru'

        lang = detect_language(user_message)
        
        # Smart date resolution: handles natural language and structured dates
        if extracted.get("pickup_date"):
            raw_date = extracted["pickup_date"]
            raw_time = extracted.get("pickup_time")
            resolved_date, resolved_time = resolve_natural_date(raw_date, raw_time)
            if resolved_date:
                extracted["pickup_date"] = resolved_date
            if resolved_time and not raw_time:
                extracted["pickup_time"] = resolved_time
        
        # Update order draft with extracted data
        # Only process products if we have meaningful product data
        if extracted.get("products"):
            # Check if extraction has actual product info (not just re-parsing context)
            has_product_names = any(p.get("name") and p.get("name").strip() for p in extracted["products"])
            has_quantities = any(p.get("quantity_kg") is not None for p in extracted["products"])
            
            # Check if this is just context re-parsing (same product names, no new quantities)
            is_context_reparse = False
            if order_draft.get("items") and has_product_names:
                existing_names = {item.get("name", "").lower() for item in order_draft["items"]}
                extracted_names = {p.get("name", "").lower() for p in extracted["products"] if p.get("name")}
                
                # If extracted names are subset of existing, check if there's new quantity data
                if extracted_names.issubset(existing_names):
                    # Check if quantities are different from existing items
                    has_new_quantity_data = False
                    if has_quantities:
                        for p in extracted["products"]:
                            if p.get("quantity_kg"):
                                # Find existing item with same name
                                existing_item = next((item for item in order_draft["items"] 
                                                     if item.get("name", "").lower() == p.get("name", "").lower()), None)
                                if existing_item and existing_item.get("quantity") != p.get("quantity_kg"):
                                    has_new_quantity_data = True
                                    break
                    
                    # If no new quantity data, it's context reparse
                    if not has_new_quantity_data:
                        is_context_reparse = True
            
            # Only process if we have NEW product data or pending_product completion
            if not is_context_reparse and (has_product_names or (pending_product and has_quantities)):
                # Check if we're updating existing product or adding new ones
                should_clear = True
                if order_draft.get("items") and has_product_names:
                    # We have existing items - only clear if explicitly changing products
                    existing_names = {item.get("name", "").lower() for item in order_draft["items"]}
                    extracted_names = {p.get("name", "").lower() for p in extracted["products"] if p.get("name")}
                    
                    # If same product names, don't clear (might be updating other fields)
                    if extracted_names.issubset(existing_names):
                        should_clear = False
                elif not has_product_names:
                    # No product names = likely just quantity update for pending_product
                    should_clear = False
                
                if should_clear:
                    # Clear items only when explicitly adding/changing products
                    order_draft["items"] = []
            
                # Validate order size first
                is_valid_size, size_error = validate_order_size(extracted["products"])
                if not is_valid_size:
                    state["messages"].append({
                        "role": "assistant",
                        "content": f"❌ {size_error}",
                        "timestamp": state["updated_at"]
                    })
                    # Don't increment clarification_count for validation errors
                    state["next_step"] = "router"
                    state["order_draft"] = order_draft
                    db.close()
                    return state
                
                for prod_info in extracted["products"]:
                    # If pending_product exists and prod_info has no name but has quantity, use pending
                    if pending_product and not prod_info.get("name") and prod_info.get("quantity_kg"):
                        # User provided weight for pending product
                        product = type('Product', (), pending_product)()
                        product.id = pending_product["product_id"]
                        product.product_id = pending_product["product_id"]
                        product.name = pending_product["name"]
                        product.price_per_kg = pending_product["price_per_kg"]
                        product.fixed_price = None
                        product.category = "cake"  # Assume cake for now
                        quantity = prod_info.get("quantity_kg")
                        
                        # Clear pending_product after use
                        if "pending_product" in order_draft:
                            del order_draft["pending_product"]
                    else:
                        # Search product in DB
                        products = search_products(db, prod_info.get("name", ""))
                        if not products:
                            continue
                        product = products[0]

                        # Determine if this is a fixed-price item (set) or per-kg item (cake)
                        is_fixed_price = bool(product.fixed_price)

                        if is_fixed_price:
                            # Fixed-price item (e.g., mini-Napoleon sets)
                            # Use quantity_sets, default to 1 if not specified
                            quantity_sets = prod_info.get("quantity_sets") or 1
                            quantity = quantity_sets  # Number of sets
                            price = float(product.fixed_price) * quantity_sets
                        else:
                            # Per-kg item (cakes)
                            quantity = prod_info.get("quantity_kg")

                            # If quantity not specified for cake, ask for it
                            if quantity is None:
                                # Check if we already have this product in the order
                                existing_product = next((item for item in order_draft.get("items", [])
                                                        if item.get("product_id") == product.product_id), None)

                                if existing_product:
                                    # Product already in order with quantity, skip asking again
                                    continue

                                # Save partial product info to remember what user wants
                                if "pending_product" not in order_draft:
                                    order_draft["pending_product"] = {
                                        "product_id": product.product_id,
                                        "name": product.name,
                                        "price_per_kg": float(product.price_per_kg) if product.price_per_kg else None
                                    }

                                # Format price without decimals
                                price_display = int(product.price_per_kg) if product.price_per_kg == int(product.price_per_kg) else product.price_per_kg

                                if lang == 'kz':
                                    weight_msg = f"Тамаша таңдау! {product.name} — {price_display}₸/кг 🍰\n\nСізге қанша кг керек? (кем дегенде 1.5 кг)"
                                else:
                                    weight_msg = f"Отличный выбор! {product.name} — {price_display}₸/кг 🍰\n\nСколько кг Вам нужно? (минимум 1.5 кг)"

                                state["messages"].append({
                                    "role": "assistant",
                                    "content": weight_msg,
                                    "timestamp": state["updated_at"]
                                })
                                state["clarification_count"] = state.get("clarification_count", 0) + 1
                                state["conversation_stage"] = "ordering"
                                state["next_step"] = "router"
                                state["order_draft"] = order_draft
                                db.close()
                                return state

                            price = calculate_price(product, quantity)

                        # Clear pending_product when we have complete product info
                        if "pending_product" in order_draft:
                            del order_draft["pending_product"]

                        # Validate product availability
                        is_available, avail_error = validate_product_availability(db, product.id)
                        if not is_available:
                            state["messages"].append({
                                "role": "assistant",
                                "content": f"❌ {avail_error}",
                                "timestamp": state["updated_at"]
                            })
                            # Don't increment clarification_count for validation errors
                            state["next_step"] = "router"
                            state["order_draft"] = order_draft
                            db.close()
                            return state

                        # Validate weight for cakes only (not for fixed-price sets)
                        if not is_fixed_price:
                            is_valid_weight, weight_error = validate_item_weight(quantity, product.category)
                            if not is_valid_weight:
                                state["messages"].append({
                                    "role": "assistant",
                                    "content": f"❌ {weight_error}",
                                    "timestamp": state["updated_at"]
                                })
                                # Don't increment clarification_count for validation errors
                                state["next_step"] = "router"
                                state["order_draft"] = order_draft
                                db.close()
                                return state

                        # Check if this product is already in items (prevent duplicates)
                        existing_item = next((item for item in order_draft["items"] if item.get("product_id") == product.product_id), None)

                        if existing_item:
                            # Update existing item instead of adding duplicate
                            existing_item["quantity"] = quantity
                            existing_item["price"] = price
                            existing_item["is_fixed_price"] = is_fixed_price
                        else:
                            # Add new item
                            order_draft["items"].append({
                                "product_id": product.product_id,
                                "name": product.name,
                                "quantity": quantity,
                                "price": price,
                                "is_fixed_price": is_fixed_price,
                                "unit_price": float(product.fixed_price) if is_fixed_price else float(product.price_per_kg)
                            })

                        # DON'T return early - continue processing other fields (date, customer, payment) below
        
        # Track validation errors to show at the end
        validation_errors = []

        if extracted.get("pickup_date"):
            # Get time if available for validation
            time_str = extracted.get("pickup_time") or order_draft.get("pickup_time")
            is_valid, error = validate_pickup_date(extracted["pickup_date"], time_str)
            if is_valid:
                order_draft["pickup_date"] = extracted["pickup_date"]
            else:
                # Don't set the date, but save error to show later
                # Continue processing other fields!
                validation_errors.append(error)
        
        if extracted.get("pickup_time"):
            order_draft["pickup_time"] = extracted["pickup_time"]
        
        if extracted.get("customer_name"):
            order_draft["customer_name"] = extracted["customer_name"]
        
        if extracted.get("customer_phone"):
            is_valid, result = validate_phone(extracted["customer_phone"])
            if is_valid:
                order_draft["customer_phone"] = result
            else:
                # Don't set the phone, but save error to show later
                validation_errors.append(result)
        
        if extracted.get("payment_method"):
            order_draft["payment_method"] = extracted["payment_method"]
        
        if extracted.get("special_requests"):
            order_draft["special_requests"] = extracted["special_requests"]
        
        # Calculate total (price is already total per item: price_per_kg * quantity)
        total = sum(item["price"] for item in order_draft.get("items", []))
        order_draft["total_amount"] = total

        logger.info(f"[ORDER_COLLECTOR] BEFORE completeness check: items={order_draft.get('items')}, date={order_draft.get('pickup_date')}, name={order_draft.get('customer_name')}")

        # Check completeness
        order_draft["completeness"] = check_order_completeness(order_draft)
        logger.info(f"[ORDER_COLLECTOR] AFTER completeness check: {order_draft['completeness']}")
        state["order_draft"] = order_draft
        
        # Check if user gave unclear/vague response
        unclear_patterns = [
            r"\bкакой[-\s]?(нибудь|то)\b",  # "какой-нибудь", "какой-то"
            r"\bлюбой\b",  # "любой торт"
            r"\bсколько[-\s]?(нибудь|то)\b",  # "сколько-нибудь"
            r"\bне\s*знаю\b",  # "не знаю"
            r"\bпосоветуй",  # "посоветуй"
            r"\bбілмеймін\b",  # "білмеймін" (не знаю)
            r"\bкеңес\b",  # "кеңес" (совет)
        ]
        
        if any(re.search(pattern, user_message.lower()) for pattern in unclear_patterns):
            # User gave vague response, provide helpful clarification
            if not order_draft["completeness"]["items"]:
                # Show full menu from DB in strict template format
                all_prods = get_all_products(db)
                menu = format_menu_for_user(all_prods, lang=lang)
                if lang == 'kz':
                    response_text = f"Қуана көмектесемін!\n\n{menu}"
                else:
                    response_text = f"С удовольствием помогу!\n\n{menu}"
            elif not order_draft["completeness"]["pickup"]:
                if lang == 'kz':
                    response_text = "Алу күні мен уақытын көрсетіңіз (мысалы: «ертең 15:00» немесе «келесі сенбі кешке»). Дайындалу уақыты кемінде 4 сағат."
                else:
                    response_text = "Пожалуйста, укажите дату и время получения (например: «завтра в 15:00» или «следующая суббота, вечером»). Минимум 4 часа на подготовку."
            elif not order_draft["completeness"]["customer"]:
                if lang == 'kz':
                    response_text = "Атыңыз бен телефон нөміріңізді жазыңыз."
                else:
                    response_text = "Пожалуйста, укажите Ваше имя и контактный телефон."
            else:
                if lang == 'kz':
                    response_text = "Тапсырысыңыздың мәліметтерін нақтылаңыз."
                else:
                    response_text = "Пожалуйста, уточните детали Вашего заказа."
            
            state["messages"].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": state["updated_at"]
            })
            state["clarification_count"] = state.get("clarification_count", 0) + 1
            state["next_step"] = "router"
            db.close()
            return state
        
        # Generate response based on what was updated and what's missing
        response_parts = []

        # Show validation errors first if any
        if validation_errors:
            response_parts.append("❌ " + "\n❌ ".join(validation_errors))

        # Check if we just added/updated products in this message
        confirmation_parts = []
        if order_draft.get("items"):
            items_list = []
            for item in order_draft["items"]:
                if item.get("is_fixed_price"):
                    # Fixed-price item (set)
                    qty = int(item['quantity'])
                    if qty == 1:
                        items_list.append(item['name'])
                    else:
                        items_list.append(f"{item['name']} × {qty}")
                else:
                    # Per-kg item (cake)
                    items_list.append(f"{item['name']} ({item['quantity']} кг)")
            items_str = ", ".join(items_list)
            total_price = sum(item.get("price", 0) for item in order_draft["items"])
            confirmation_parts.append(f"🍰 {'Тапсырыс' if lang == 'kz' else 'Заказ'}: {items_str}")
            if total_price > 0:
                confirmation_parts.append(f"💰 {'Сомасы' if lang == 'kz' else 'Сумма'}: {total_price:.0f}₸")

        # Build list of missing fields
        missing = []
        if not order_draft["completeness"]["items"]:
            if lang == 'kz':
                missing.append("• Қай торт және қанша кг керек?")
            else:
                missing.append("• Какой торт и сколько кг Вам нужно?")
        if not order_draft["completeness"]["pickup"]:
            if lang == 'kz':
                missing.append("• Қай күні және сағат нешеде? («ертең», «келесі сенбі» деп жазуға болады)")
            else:
                missing.append("• На какую дату и время? (можно написать «завтра», «послезавтра» и т.д.)")
        if not order_draft["completeness"]["customer"]:
            if lang == 'kz':
                missing.append("• Атыңыз бен телефон нөміріңіз?")
            else:
                missing.append("• Ваше имя и телефон?")
        if not order_draft["completeness"]["payment"]:
            if lang == 'kz':
                missing.append("• Төлем тәсілі? (алдын ала төлем / қолма-қол)")
            else:
                missing.append("• Способ оплаты? (предоплата / наличные при получении)")

        if missing:
            # Still missing some fields
            ask_more = "\nТағы нақтылаңыз:" if lang == 'kz' else "\nПожалуйста, уточните ещё:"
            ask_only = "Нақтылаңыз:" if lang == 'kz' else "Пожалуйста, уточните:"
            if confirmation_parts:
                response_parts.append("\n".join(confirmation_parts))
                response_parts.append(f"{ask_more}\n" + "\n".join(missing))
            else:
                response_parts.append(f"{ask_only}\n" + "\n".join(missing))
            state["conversation_stage"] = "ordering"
        else:
            # Order complete, move to confirmation
            from app.agents.tools.order_tools import format_order_summary
            summary = format_order_summary(order_draft)
            response_parts.append(summary)
            if lang == 'kz':
                response_parts.append("\n✅ Бәрі дұрыс па? Тапсырысты растаңыз.")
            else:
                response_parts.append("\n✅ Всё верно? Пожалуйста, подтвердите заказ.")
            state["conversation_stage"] = "confirming"

        response_text = "\n\n".join(response_parts)
        
        state["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": state["updated_at"]
        })
        
        state["next_step"] = "router"
        
    finally:
        db.close()
    
    return state
