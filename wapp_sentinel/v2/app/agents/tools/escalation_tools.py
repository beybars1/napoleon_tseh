"""
Escalation Tools - Logic for flagging conversations for human takeover
"""
from typing import Optional


# Escalation thresholds
MAX_CLARIFICATIONS = 5  # Increased from 3 - only for true clarifications (not validation errors)
ESCALATION_KEYWORDS = [
    "кастомизация", "особый дизайн", "специальный декор", "индивидуальный",
    "доставка", "курьер", "привезите", "доставить",
    "жалоба", "недовольн", "плохо", "ужасно", "руководитель", "позовите менеджера", "соединить с менеджером"
]


def should_escalate(
    state: dict,
    current_intent: str,
    message: str
) -> tuple[bool, Optional[str]]:
    """
    Determine if conversation should be escalated to human
    
    Returns:
        (should_escalate, reason)
    """
    
    # Check clarification count
    if state.get("clarification_count", 0) >= MAX_CLARIFICATIONS:
        return True, f"Превышен лимит уточнений ({MAX_CLARIFICATIONS})"
    
    # Check for customization requests
    if current_intent == "customization_request":
        return True, "Запрос на кастомную продукцию"
    
    # Check for delivery inquiries (pickup only policy)
    if current_intent == "delivery_inquiry":
        return True, "Запрос на доставку"
    
    # Check for complaints
    if current_intent == "complaint":
        return True, "Жалоба клиента"
    
    # Check for escalation keywords in message
    message_lower = message.lower()
    for keyword in ESCALATION_KEYWORDS:
        if keyword in message_lower:
            return True, f"Ключевое слово эскалации: {keyword}"
    
    return False, None


def format_escalation_summary(state: dict) -> str:
    """Format conversation context for human agent"""
    lines = [
        "🚨 Эскалация на оператора",
        f"Причина: {state.get('escalation_reason', 'N/A')}",
        f"Чат: {state.get('chat_id')}",
        f"Кол-во сообщений: {len(state.get('messages', []))}",
        "",
        "📜 Последние сообщения:"
    ]
    
    for msg in state.get("messages", [])[-5:]:
        role_emoji = "👤" if msg["role"] == "user" else "🤖"
        lines.append(f"{role_emoji} {msg['content'][:100]}")
    
    if state.get("order_draft"):
        from app.agents.tools.order_tools import format_order_summary
        lines.append("\n" + format_order_summary(state["order_draft"]))
    
    return "\n".join(lines)


def increment_clarification(state: dict) -> dict:
    """Increment clarification counter"""
    state["clarification_count"] = state.get("clarification_count", 0) + 1
    return state
