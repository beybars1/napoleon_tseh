"""
Acknowledgment Node - Handles simple acknowledgments without repeating questions
"""
from app.agents.state import ConversationState


def acknowledgment_node(state: ConversationState) -> ConversationState:
    """
    Handle acknowledgments like "хорошо", "ок", "понятно"
    Also handles mid-conversation greetings (when user says "привет" during active order)
    Also handles reset commands ("сброс", "отмена")
    - If there was previous error/validation message, don't repeat all questions
    - Just provide brief helpful response
    """
    
    order_draft = state.get("order_draft", {})
    conversation_stage = state.get("conversation_stage", "inquiry")
    last_intent = state.get("last_intent")
    user_message = state["messages"][-1]["content"].lower()
    
    # Check for reset commands
    import re
    reset_patterns = [r"\bсброс\b", r"\bзаново\b", r"\bотмена\b", r"\bотменить\b", r"\bс\s*нуля\b"]
    if any(re.search(pattern, user_message) for pattern in reset_patterns):
        response_text = "Хорошо, заказ отменен. Начнем заново! 😊\n\nКакой торт вас интересует?"
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
        return state
    
    # Check what's missing in order
    completeness = order_draft.get("completeness", {})
    
    # If this is mid-conversation greeting, be friendly but continue
    if last_intent == "greeting":
        if conversation_stage == "ordering":
            response_text = "Привет! 👋 Продолжим оформление заказа?"
        elif conversation_stage == "confirming":
            response_text = "Здравствуйте! 👋 Подтверждаете заказ?"
        else:
            response_text = "Привет! 👋 Чем могу помочь?"
    # Generate contextual response based on what's missing
    elif conversation_stage == "ordering":
        if not completeness.get("items"):
            response_text = "Какой торт и сколько кг вам нужно?"
        elif not completeness.get("pickup"):
            response_text = "На какую дату и время нужен торт?"
        elif not completeness.get("customer"):
            response_text = "Укажите ваше имя и телефон."
        elif not completeness.get("payment"):
            response_text = "Способ оплаты: предоплата 100% или наличные при получении?"
        else:
            response_text = "Уточните детали заказа."
    else:
        response_text = "Чем ещё могу помочь? 😊"
    
    state["messages"].append({
        "role": "assistant",
        "content": response_text,
        "timestamp": state["updated_at"]
    })
    
    state["next_step"] = "router"
    
    return state
