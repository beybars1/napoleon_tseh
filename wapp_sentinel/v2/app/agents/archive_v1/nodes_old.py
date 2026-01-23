"""Node implementations for LangGraph order collection workflow"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)


def greet_customer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initial greeting node. Welcomes customer and explains what the bot can do.
    """
    greeting = (
        "Добро пожаловать! 👋\n\n"
        "Я помогу вам оформить заказ. Я могу принять ваш заказ на продукты "
        "и согласовать время доставки.\n\n"
        "Расскажите, что бы вы хотели заказать?"
    )
    
    state["messages"].append({"role": "assistant", "content": greeting})
    state["last_assistant_message"] = greeting
    state["current_step"] = "collect_items"
    
    return state


def collect_items(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect items from customer message using LLM to extract structured data.
    """
    user_message = state["last_user_message"]
    
    # Build context from conversation history
    context_messages = []
    for msg in state["messages"][-5:]:  # Last 5 messages for context
        if msg["role"] == "user":
            context_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            context_messages.append(AIMessage(content=msg["content"]))
    
    # System prompt for item extraction
    system_prompt = f"""Ты - ассистент по приему заказов. Текущая дата: {datetime.now().strftime('%Y-%m-%d')}.

Твоя задача - извлечь список товаров из сообщения клиента.

Извлеки товары в формате JSON:
{{
    "items": [
        {{"name": "название товара", "quantity": "количество", "notes": "примечания (если есть)"}},
        ...
    ],
    "has_items": true/false
}}

Если товары упомянуты - установи has_items=true и заполни список.
Если товары НЕ упомянуты - установи has_items=false и попроси клиента указать товары.

Примеры:
- "Хочу заказать 2кг помидоров и 1кг огурцов" → has_items=true
- "Да, оформите заказ" → has_items=false (нет конкретных товаров)
- "Мне нужно" → has_items=false (незавершенное предложение)"""

    messages = [
        SystemMessage(content=system_prompt),
        *context_messages,
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        result = json.loads(response.content)
        
        if result.get("has_items"):
            # Successfully extracted items
            state["items"] = result["items"]
            state["has_items"] = True
            
            # Confirm items with customer
            items_list = "\n".join([f"• {item['name']} - {item['quantity']}" for item in result["items"]])
            confirmation = f"Отлично! Вы хотите заказать:\n{items_list}\n\nНа какую дату и время нужна доставка?"
            
            state["messages"].append({"role": "assistant", "content": confirmation})
            state["last_assistant_message"] = confirmation
            state["current_step"] = "collect_delivery"
        else:
            # Need more information
            clarification = "Пожалуйста, укажите конкретные товары и их количество. Например: '2кг помидоров, 1кг огурцов, 500г зелени'"
            
            state["messages"].append({"role": "assistant", "content": clarification})
            state["last_assistant_message"] = clarification
            state["needs_clarification"] = True
            state["clarification_topic"] = "items"
            state["retry_count"] += 1
    
    except Exception as e:
        # Error handling
        error_msg = "Извините, не смог понять список товаров. Пожалуйста, перечислите товары и количество."
        state["messages"].append({"role": "assistant", "content": error_msg})
        state["last_assistant_message"] = error_msg
        state["needs_clarification"] = True
        state["clarification_topic"] = "items"
    
    return state


def collect_delivery(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect delivery date, time, and address using LLM.
    """
    user_message = state["last_user_message"]
    
    system_prompt = f"""Ты - ассистент по приему заказов. Текущая дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}.

Извлеки информацию о доставке из сообщения клиента в формат JSON:
{{
    "delivery_datetime": "YYYY-MM-DD HH:MM" или null,
    "delivery_address": "адрес" или null,
    "has_delivery_info": true/false
}}

Правила:
- Если указана дата/время - распарси в формат YYYY-MM-DD HH:MM
- "Сегодня" = текущая дата
- "Завтра" = текущая дата + 1 день
- Если время не указано, установи 12:00
- Если адрес указан - сохрани его
- has_delivery_info=true только если есть хотя бы дата

Примеры:
- "Завтра в 14:00 на ул.Ленина 5" → delivery_datetime="2025-11-06 14:00", delivery_address="ул.Ленина 5", has_delivery_info=true
- "На завтра" → delivery_datetime="2025-11-06 12:00", has_delivery_info=true
- "Не знаю" → has_delivery_info=false"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        result = json.loads(response.content)
        
        if result.get("has_delivery_info"):
            state["delivery_datetime"] = result.get("delivery_datetime")
            state["delivery_address"] = result.get("delivery_address")
            state["has_delivery_info"] = True
            
            # Confirm and ask about payment
            confirmation = f"Понял, доставка на {result['delivery_datetime']}"
            if result.get("delivery_address"):
                confirmation += f" по адресу {result['delivery_address']}"
            confirmation += ".\n\nБудете оплачивать сейчас или при получении?"
            
            state["messages"].append({"role": "assistant", "content": confirmation})
            state["last_assistant_message"] = confirmation
            state["current_step"] = "collect_payment"
        else:
            clarification = "Пожалуйста, укажите дату и желаемое время доставки. Например: 'завтра в 15:00' или '6 ноября в 10:00'"
            state["messages"].append({"role": "assistant", "content": clarification})
            state["last_assistant_message"] = clarification
            state["needs_clarification"] = True
            state["clarification_topic"] = "delivery"
    
    except Exception as e:
        error_msg = "Не смог определить время доставки. Укажите, пожалуйста, дату и время."
        state["messages"].append({"role": "assistant", "content": error_msg})
        state["last_assistant_message"] = error_msg
        state["needs_clarification"] = True
    
    return state


def collect_payment(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine payment status from customer message.
    """
    user_message = state["last_user_message"].lower()
    
    # Simple keyword-based detection
    if any(word in user_message for word in ["оплатил", "оплачу сейчас", "оплачено", "перевел", "переведу"]):
        payment_status = "paid"
        response = "Отлично, оплата учтена."
    elif any(word in user_message for word in ["при получении", "наличными", "при доставке", "курьеру"]):
        payment_status = "unpaid"
        response = "Хорошо, оплата при получении."
    else:
        payment_status = "unknown"
        response = "Принято."
    
    state["payment_status"] = payment_status
    state["has_payment_info"] = True
    
    # Ask for contact info
    response += "\n\nПожалуйста, укажите ваше имя и номер телефона для связи."
    
    state["messages"].append({"role": "assistant", "content": response})
    state["last_assistant_message"] = response
    state["current_step"] = "collect_contacts"
    
    return state


def collect_contacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract customer name and phone number(s).
    """
    user_message = state["last_user_message"]
    
    system_prompt = """Извлеки контактную информацию из сообщения в JSON:
{
    "client_name": "имя" или null,
    "client_phone": "основной телефон" или null,
    "additional_phone": "доп. телефон" или null,
    "has_contact_info": true/false
}

has_contact_info=true если есть хотя бы имя или телефон.

Примеры:
- "Иван, 87001234567" → client_name="Иван", client_phone="87001234567", has_contact_info=true
- "87001234567" → client_phone="87001234567", has_contact_info=true
- "Позже скажу" → has_contact_info=false"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        result = json.loads(response.content)
        
        if result.get("has_contact_info"):
            state["client_name"] = result.get("client_name")
            state["client_phone"] = result.get("client_phone")
            state["additional_phone"] = result.get("additional_phone")
            state["has_contact_info"] = True
            state["current_step"] = "validate"
        else:
            clarification = "Пожалуйста, укажите имя и номер телефона."
            state["messages"].append({"role": "assistant", "content": clarification})
            state["last_assistant_message"] = clarification
            state["needs_clarification"] = True
            state["clarification_topic"] = "contacts"
    
    except Exception as e:
        error_msg = "Не смог определить контакты. Укажите, пожалуйста, имя и телефон."
        state["messages"].append({"role": "assistant", "content": error_msg})
        state["last_assistant_message"] = error_msg
        state["needs_clarification"] = True
    
    return state


def validate_order(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all required information is collected.
    """
    missing = []
    
    if not state.get("has_items"):
        missing.append("товары")
    if not state.get("has_delivery_info"):
        missing.append("дата/время доставки")
    if not state.get("has_contact_info"):
        missing.append("контактная информация")
    
    if missing:
        # Something is missing
        state["order_validated"] = False
        state["needs_clarification"] = True
        state["clarification_topic"] = ", ".join(missing)
        state["current_step"] = "clarify"
        
        msg = f"Для оформления заказа нужна еще информация: {', '.join(missing)}."
        state["messages"].append({"role": "assistant", "content": msg})
        state["last_assistant_message"] = msg
    else:
        # All data collected
        state["order_validated"] = True
        state["current_step"] = "confirm"
    
    return state


def handle_clarification(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle requests for missing information.
    """
    topic = state.get("clarification_topic", "")
    
    if "товары" in topic:
        state["current_step"] = "collect_items"
    elif "доставк" in topic:
        state["current_step"] = "collect_delivery"
    elif "контакт" in topic:
        state["current_step"] = "collect_contacts"
    else:
        # Default to validation
        state["current_step"] = "validate"
    
    state["needs_clarification"] = False
    return state


def confirm_with_customer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Show order summary and ask for confirmation.
    """
    # Build order summary
    items_text = "\n".join([f"• {item['name']} - {item['quantity']}" for item in state.get("items", [])])
    
    summary = f"""Подтвердите заказ:

📦 Товары:
{items_text}

🚚 Доставка: {state.get('delivery_datetime', 'не указано')}
{f"📍 Адрес: {state['delivery_address']}" if state.get('delivery_address') else ''}

💳 Оплата: {state.get('payment_status', 'не указано')}

👤 Контакт: {state.get('client_name', '')} {state.get('client_phone', '')}

Все верно? (Да/Нет)"""

    state["messages"].append({"role": "assistant", "content": summary})
    state["last_assistant_message"] = summary
    state["current_step"] = "awaiting_confirmation"
    
    return state


def save_order(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark order as confirmed and ready to save to database.
    This is handled by the worker after graph execution.
    """
    state["order_confirmed"] = True
    state["current_step"] = "completed"
    
    thanks = "Спасибо! Ваш заказ принят. Мы свяжемся с вами для подтверждения."
    state["messages"].append({"role": "assistant", "content": thanks})
    state["last_assistant_message"] = thanks
    
    return state


def handle_rejection(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle when customer rejects the order or wants to make changes.
    """
    msg = "Хорошо, давайте изменим заказ. Что нужно исправить?"
    state["messages"].append({"role": "assistant", "content": msg})
    state["last_assistant_message"] = msg
    state["order_confirmed"] = False
    state["current_step"] = "collect_items"  # Start over
    
    return state
