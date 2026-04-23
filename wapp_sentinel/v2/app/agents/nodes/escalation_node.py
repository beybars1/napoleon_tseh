"""
Escalation Node - Transfers conversation to human operator
"""
from app.agents.state import ConversationState
from app.agents.tools.escalation_tools import format_escalation_summary


def escalation_node(state: ConversationState) -> ConversationState:
    """
    Handle escalation to human operator
    - Set flagged_for_human = True
    - Send transfer message to customer
    - Log escalation context
    - Mark conversation stage as 'escalated'
    """
    
    # Generate escalation summary for internal logging
    summary = format_escalation_summary(state)
    
    # Log to console (in production, send to operator dashboard)
    print(f"\n{'='*50}")
    print(summary)
    print(f"{'='*50}\n")
    
    # Message to customer
    escalation_message = f"""Благодарим Вас за обращение! 

Ваш запрос требует консультации менеджера. Переключаем Вас на оператора — он свяжется с Вами в ближайшее время.

Пожалуйста, ожидайте ответа 🙏"""
    
    state["messages"].append({
        "role": "assistant",
        "content": escalation_message,
        "timestamp": state["updated_at"]
    })
    
    state["flagged_for_human"] = True
    state["conversation_stage"] = "escalated"
    state["next_step"] = "end"
    
    return state
