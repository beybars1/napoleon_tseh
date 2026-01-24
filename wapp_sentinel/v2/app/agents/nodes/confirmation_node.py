"""
Confirmation Node - Handles order confirmation
"""
import os
import json
import re
from openai import OpenAI
from datetime import datetime, timezone
from app.agents.state import ConversationState
from app.agents.tools.order_tools import format_order_summary
from app.database.database import SessionLocal
from app.database.models import AIGeneratedOrder, Conversation

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def normalize_date_string(date_str: str | None) -> str | None:
    if not date_str:
        return None
    value = date_str.strip().replace("/", ".")

    if re.match(r"^\d{1,2}\.\d{1,2}\.?$", value):
        day, month = value.rstrip(".").split(".")
        year = str(datetime.now().year)
        return f"{day.zfill(2)}.{month.zfill(2)}.{year}"

    if re.match(r"^\d{1,2}\s+\d{1,2}(\s+\d{2,4})?$", value):
        parts = value.split()
        day = parts[0].zfill(2)
        month = parts[1].zfill(2)
        year = parts[2] if len(parts) > 2 else str(datetime.now().year)
        if len(year) == 2:
            year = "20" + year
        return f"{day}.{month}.{year}"

    return value


def normalize_time_string(time_str: str | None) -> str | None:
    if not time_str:
        return None
    value = time_str.strip()
    value = re.sub(r"[\.\s]+", ":", value)
    if re.match(r"^\d{1,2}:\d{2}$", value):
        hours, minutes = value.split(":")
        return f"{hours.zfill(2)}:{minutes}"
    return value


def find_target_item_index(order_draft: dict, message_lower: str, replace_from: str | None = None) -> int | None:
    items = order_draft.get("items", [])
    if not items:
        return None

    if replace_from:
        needle = replace_from.lower().strip()
        for idx, item in enumerate(items):
            if needle and needle in item.get("name", "").lower():
                return idx

    keywords = [
        "клубничн", "шоколадн", "ванильн", "кофейн", "карамельн",
        "малинов", "фисташков", "классическ"
    ]

    for keyword in keywords:
        if keyword in message_lower:
            for idx, item in enumerate(items):
                if keyword in item.get("name", "").lower():
                    return idx

    if "вместо" in message_lower:
        non_fixed = [i for i, item in enumerate(items) if not item.get("is_fixed_price")]
        if len(non_fixed) == 1:
            return non_fixed[0]

    return None


def confirmation_node(state: ConversationState) -> ConversationState:
    """
    Handle order confirmation
    - Check if user confirms (да, подтверждаю, верно)
    - If confirmed: finalize order, send to order_processor_queue
    - If rejected/modified: return to order_collector
    """
    
    db = SessionLocal()
    try:
        user_message = state["messages"][-1]["content"].lower()
        order_draft = state.get("order_draft", {})
        
        # Check if user wants to start completely from scratch
        reset_patterns = [r"\bзаново\b", r"\bсначала\b", r"\bс\s*нуля\b", r"\bотменить\b"]
        if any(re.search(pattern, user_message) for pattern in reset_patterns):
            # Full reset - cancel current order and start fresh
            conversation_id = state.get("conversation_id")
            
            ai_order = db.query(AIGeneratedOrder).filter(
                AIGeneratedOrder.conversation_id == conversation_id,
                AIGeneratedOrder.validation_status == 'pending'
            ).first()
            
            if ai_order:
                ai_order.validation_status = "cancelled"
                db.commit()
            
            response_text = "Хорошо, начнем заново! 😊\n\nКакой торт вас интересует?"
            state["conversation_stage"] = "inquiry"
            state["clarification_count"] = 0
            state["order_draft"] = {
                "items": [],
                "completeness": {"items": False, "pickup": False, "customer": False, "payment": False}
            }
            state["messages"].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": state["updated_at"]
            })
            state["next_step"] = "router"
            db.close()
            return state
        
        # Classify confirmation intent
        confirmation_prompt = f"""Определи намерение клиента:

Сообщение: "{user_message}"

Варианты:
1. "confirmed" - клиент ЯВНО подтверждает заказ словами: да, подтверждаю, верно, все правильно, ок, хорошо, согласен
2. "rejected" - клиент отказывается (нет, отмена, не хочу)
3. "modification" - клиент хочет изменить ИЛИ предоставляет новые данные (дату, время, имя, телефон, оплату)
4. "unclear" - непонятно

ПРАВИЛА:
- Если сообщение содержит дату (23.01, 25 января) → "modification"
- Если сообщение содержит время (15:00, 20 00) → "modification"
- Если сообщение содержит телефон (+7700, 8700) → "modification"
- Если сообщение содержит "другая", "другое", "другой" → "modification"
- Если сообщение содержит "изменить", "поменять", "можно" → "modification"
- ТОЛЬКО если клиент говорит "да", "подтверждаю", "верно", "ок" БЕЗ новых данных → "confirmed"

Отвечай только одним словом: confirmed/rejected/modification/unclear"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты классификатор намерений. Отвечай одним словом."},
                {"role": "user", "content": confirmation_prompt}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        intent = response.choices[0].message.content.strip().lower()
        
        if intent == "confirmed":
            # Finalize order
            conversation_id = state.get("conversation_id")
            
            # Get or create AIGeneratedOrder
            ai_order = db.query(AIGeneratedOrder).filter(
                AIGeneratedOrder.conversation_id == conversation_id,
                AIGeneratedOrder.validation_status == 'pending'
            ).first()
            
            if not ai_order:
                # Create new order
                ai_order = AIGeneratedOrder(
                    conversation_id=conversation_id,
                    chat_id=state.get("chat_id"),
                    items=order_draft.get("items", []),
                    validation_status="pending"
                )
                db.add(ai_order)
            
            # Update order details
            ai_order.validation_status = "pending_validation"
            ai_order.client_name = order_draft.get("customer_name")
            ai_order.client_phone = order_draft.get("customer_phone")
            ai_order.payment_status = order_draft.get("payment_method")
            ai_order.notes = order_draft.get("special_requests")
            ai_order.items = order_draft.get("items", [])
            
            # Calculate total
            total = sum(item.get("price", 0) for item in order_draft.get("items", []))
            ai_order.total_amount = total
            
            # Parse pickup datetime
            if order_draft.get("pickup_date") and order_draft.get("pickup_time"):
                date_str = f"{order_draft['pickup_date']} {order_draft['pickup_time']}"
                try:
                    ai_order.estimated_delivery_datetime = datetime.strptime(date_str, "%d.%m.%Y %H:%M").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            
            ai_order.confirmed_at = datetime.now(timezone.utc)
            db.commit()
            
            # Update conversation state
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                conversation.conversation_stage = "completed"
                db.commit()
            
            # TODO: Send to order_processor_queue for validation
            
            response_text = f"""✅ Заказ подтвержден!

📱 Номер заказа: #{ai_order.id if ai_order else 'N/A'}

Мы свяжемся с вами в течение 15 минут для:
• Подтверждения деталей
• Отправки реквизитов для предоплаты (если выбрана)
• Уточнения адреса самовывоза

Спасибо за заказ! 🍰"""
            
            state["conversation_stage"] = "completed"
            
        elif intent == "modification":
            # Revert AIGeneratedOrder status back to pending for editing
            conversation_id = state.get("conversation_id")
            ai_order = db.query(AIGeneratedOrder).filter(
                AIGeneratedOrder.conversation_id == conversation_id
            ).order_by(AIGeneratedOrder.created_at.desc()).first()

            if ai_order and ai_order.validation_status in ['pending_validation', 'validated']:
                ai_order.validation_status = "pending"  # Allow editing
                db.commit()

            # Get current order items for context
            current_items = order_draft.get("items", [])
            items_context = ", ".join([f"{item.get('name')} ({item.get('quantity')} кг)" for item in current_items if not item.get('is_fixed_price')])
            items_context += ", " + ", ".join([item.get('name') for item in current_items if item.get('is_fixed_price')])

            # Try to extract new values directly from the modification message
            extraction_prompt = f"""Извлеки новые данные из сообщения клиента, который хочет изменить заказ.

Сообщение: "{state["messages"][-1]["content"]}"

ТЕКУЩИЙ ЗАКАЗ: {items_context}

Формат ответа (JSON):
{{
  "field": "date|time|items|customer|payment|all|unclear",
    "replace_from": null,
  "new_date": null,
  "new_time": null,
  "new_product": null,
  "new_quantity_kg": null,
  "new_name": null,
  "new_phone": null,
  "new_payment": null
}}

ПРАВИЛА ОПРЕДЕЛЕНИЯ FIELD:
1. Изменение КОЛИЧЕСТВА торта (например "клубничный на 6 кг") → field = "items"
2. Замена торта на другой → field = "items"
3. Изменение даты → field = "date"
4. Изменение времени → field = "time"
5. Изменение имени/телефона → field = "customer"
6. Изменение оплаты → field = "payment"
7. Если есть "вместо X" → replace_from = "X"

ПРАВИЛА ДЛЯ ИЗМЕНЕНИЯ ТОВАРОВ (field = "items"):
- "клубничный на 6 кг вместо 3" → new_product = "Торт Наполеон Клубничный", new_quantity_kg = 6
- "поменять клубничный на шоколадный" → new_product = "Торт Наполеон Шоколадный", new_quantity_kg = (сохранить текущий вес)
- Используй ТОЧНЫЕ названия: "Торт Наполеон Клубничный", "Торт Наполеон Ванильный" и т.д.

Примеры:
"клубничный на 6 кг вместо 3кг" → {{"field": "items", "new_product": "Торт Наполеон Клубничный", "new_quantity_kg": 6, ...rest null}}
"поменять время на 20:00" → {{"field": "time", "new_time": "20:00", ...rest null}}
"дату на 26 января" → {{"field": "date", "new_date": "26.01.2026", ...rest null}}

Отвечай ТОЛЬКО валидным JSON."""

            extract_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты экстрактор данных. Отвечай только валидным JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )

            try:
                extracted = json.loads(extract_response.choices[0].message.content.strip())
            except json.JSONDecodeError:
                extracted = {"field": "unclear"}

            mod_field = extracted.get("field", "unclear")
            updated = False

            replace_from = extracted.get("replace_from")
            if replace_from:
                replace_from = replace_from.strip()

            normalized_date = normalize_date_string(extracted.get("new_date"))
            normalized_time = normalize_time_string(extracted.get("new_time"))

            # Apply extracted changes directly to order_draft
            if normalized_time:
                order_draft["pickup_time"] = normalized_time
                updated = True
            if normalized_date:
                order_draft["pickup_date"] = normalized_date
                updated = True
            if extracted.get("new_name"):
                order_draft["customer_name"] = extracted["new_name"]
                updated = True
            if extracted.get("new_phone"):
                from app.agents.tools.order_tools import validate_phone
                is_valid, result = validate_phone(extracted["new_phone"])
                if is_valid:
                    order_draft["customer_phone"] = result
                    updated = True
            if extracted.get("new_payment"):
                order_draft["payment_method"] = extracted["new_payment"]
                updated = True

            # Handle item modifications (quantity change or product replacement)
            if extracted.get("new_product") or extracted.get("new_quantity_kg"):
                from app.agents.tools.product_tools import search_products, calculate_price
                target_index = find_target_item_index(order_draft, user_message, replace_from)

                if target_index is None:
                    non_fixed = [i for i, item in enumerate(order_draft.get("items", [])) if not item.get("is_fixed_price")]
                    if len(non_fixed) == 1:
                        target_index = non_fixed[0]

                new_product_name = extracted.get("new_product")
                new_qty = extracted.get("new_quantity_kg")

                if new_product_name:
                    products = search_products(db, new_product_name)
                    if products:
                        product = products[0]

                        if target_index is not None and new_qty is None:
                            new_qty = order_draft["items"][target_index].get("quantity")

                        if product.fixed_price:
                            if new_qty is None:
                                new_qty = 1
                            price = calculate_price(product, new_qty)
                        else:
                            if new_qty is None:
                                new_qty = None
                            price = calculate_price(product, new_qty) if new_qty is not None else None

                        if new_qty is not None and price is not None and target_index is not None:
                            order_draft["items"][target_index].update({
                                "name": product.name,
                                "product_id": product.product_id,
                                "quantity": new_qty,
                                "price": price,
                                "is_fixed_price": bool(product.fixed_price),
                                "unit_price": float(product.fixed_price) if product.fixed_price else float(product.price_per_kg)
                            })
                            updated = True
                elif new_qty is not None and target_index is not None:
                    item = order_draft["items"][target_index]
                    if not item.get("is_fixed_price"):
                        item["quantity"] = new_qty
                        item["price"] = item.get("unit_price", 0) * new_qty
                        updated = True

                if updated:
                    total = sum(i.get("price", 0) for i in order_draft.get("items", []))
                    order_draft["total_amount"] = total

            # If we extracted and applied new values, show updated summary for confirmation
            if updated:
                state["order_draft"] = order_draft
                summary = format_order_summary(order_draft)
                response_text = f"{summary}\n\n✅ Все верно? Подтвердите заказ."
                state["conversation_stage"] = "confirming"
                state["next_step"] = "end"
            else:
                # No values extracted, ask for specific field based on what user wants to change
                if mod_field == "items":
                    response_text = "Хорошо, скажите какой торт и сколько кг хотите вместо текущего заказа?"
                elif mod_field == "date":
                    response_text = "Хорошо, укажите новую дату получения (например: 25.01.2026)."
                elif mod_field == "time":
                    response_text = "Хорошо, укажите новое время получения (например: 15:00)."
                elif mod_field == "customer":
                    response_text = "Хорошо, укажите новое имя и телефон."
                elif mod_field == "payment":
                    response_text = "Хорошо, выберите способ оплаты: предоплата 100% или наличные при получении."
                else:
                    response_text = "Что именно хотите изменить? (дату, время, торт, имя, телефон, оплату)"

                # Stay in confirming stage so next message comes back here
                state["conversation_stage"] = "confirming"
                state["next_step"] = "end"
            
        elif intent == "rejected":
            # Cancel order - clear order_draft in DB
            conversation_id = state.get("conversation_id")
            
            ai_order = db.query(AIGeneratedOrder).filter(
                AIGeneratedOrder.conversation_id == conversation_id,
                AIGeneratedOrder.validation_status == 'pending'
            ).first()
            
            if ai_order:
                ai_order.validation_status = "cancelled"
                db.commit()
            
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if conversation:
                conversation.conversation_stage = "inquiry"
                db.commit()
            
            response_text = "Хорошо, заказ отменен. Если передумаете — напишите снова! 😊"
            state["conversation_stage"] = "inquiry"
            state["order_draft"] = {
                "items": [],
                "completeness": {"items": False, "pickup": False, "customer": False, "payment": False}
            }
            
        else:
            # Unclear, explain and ask again
            summary = format_order_summary(order_draft)
            
            # Check if there are any pre-filled fields from previous orders
            has_prefilled = any([
                order_draft.get("pickup_date"),
                order_draft.get("customer_name"),
                order_draft.get("customer_phone"),
                order_draft.get("payment_method")
            ])
            
            if has_prefilled and not order_draft.get("completeness", {}).get("customer"):
                # Explain where data came from
                response_text = f"""{summary}

ℹ️ Некоторые данные заполнены из предыдущих заказов для удобства.

❓ Пожалуйста, подтвердите:
• Напишите "Да" или "Подтверждаю" если все верно
• Или скажите, что хотите изменить (например: "другую дату", "другой телефон")
• Или "Заново" чтобы начать с нуля"""
            else:
                response_text = f"""{summary}

❓ Пожалуйста, подтвердите:
• Напишите "Да" или "Подтверждаю" для оформления
• Или скажите, что хотите изменить"""
            state["clarification_count"] = state.get("clarification_count", 0) + 1
        
        state["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": state["updated_at"]
        })
        
        state["next_step"] = "end"
        
    finally:
        db.close()
    
    return state
