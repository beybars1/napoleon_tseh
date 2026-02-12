"""
Order Graph - LangGraph workflow for v2 intent-driven architecture
"""
import os
from langgraph.graph import StateGraph, END
from app.agents.state import ConversationState
from app.agents.nodes.intent_classifier import classify_intent

# Configurable edit window (in hours) - can be set via environment variable
ORDER_EDIT_WINDOW_HOURS = int(os.getenv("ORDER_EDIT_WINDOW_HOURS", "2"))
from app.agents.nodes.greeting_node import greeting_node
from app.agents.nodes.product_inquiry_node import product_inquiry_node
from app.agents.nodes.order_collector_node import order_collector_node
from app.agents.nodes.confirmation_node import confirmation_node
from app.agents.nodes.acknowledgment_node import acknowledgment_node
from app.agents.nodes.escalation_node import escalation_node
from app.agents.nodes.info_provider_node import info_provider_node
from app.agents.nodes.small_talk_node import small_talk_node
from app.agents.tools.escalation_tools import should_escalate


def handle_order_reset(state: ConversationState, confirmed: bool = False) -> ConversationState:
    """
    Handle order reset - cancel current order and start fresh.
    If not confirmed, ask for confirmation first.
    """
    from app.database.database import SessionLocal
    from app.database.models import AIGeneratedOrder

    order_draft = state.get("order_draft", {})
    has_order = bool(order_draft.get("items"))

    # If no active order, just acknowledge and continue
    if not has_order:
        state["conversation_stage"] = "inquiry"
        state["messages"].append({
            "role": "assistant",
            "content": "У Вас пока нет активного заказа. Какой торт Вас интересует?",
            "timestamp": state["updated_at"]
        })
        state["next_step"] = "end"
        return state

    # If not confirmed yet, ask for confirmation
    if not confirmed:
        from app.agents.tools.order_tools import format_order_summary
        summary = format_order_summary(order_draft)
        state["messages"].append({
            "role": "assistant",
            "content": f"Вы хотите отменить текущий заказ?\n\n{summary}\n\n❓ Напишите «Да, отменить» для отмены или «Нет», чтобы продолжить.",
            "timestamp": state["updated_at"]
        })
        state["conversation_stage"] = "reset_confirmation"
        state["next_step"] = "end"
        return state

    # Confirmed - cancel order in DB
    db = SessionLocal()
    try:
        conversation_id = state.get("conversation_id")
        ai_order = db.query(AIGeneratedOrder).filter(
            AIGeneratedOrder.conversation_id == conversation_id,
            AIGeneratedOrder.validation_status.in_(['pending', 'pending_validation', 'validated'])
        ).first()

        if ai_order:
            ai_order.validation_status = "cancelled"
            db.commit()
    finally:
        db.close()

    state["conversation_stage"] = "inquiry"
    state["clarification_count"] = 0
    state["order_draft"] = {
        "items": [],
        "completeness": {"items": False, "pickup": False, "customer": False, "payment": False}
    }
    state["messages"].append({
        "role": "assistant",
        "content": "Хорошо, заказ отменён. Начнём заново! 😊\n\nКакой торт Вас интересует?",
        "timestamp": state["updated_at"]
    })
    state["next_step"] = "end"
    return state


def router_node(state: ConversationState) -> ConversationState:
    """
    Router node - Classifies intent and routes to specialized handler
    Uses hybrid approach: fast regex for obvious cases + LLM for nuanced understanding
    """
    import re

    # Get last user message
    user_message = state["messages"][-1]["content"]
    user_message_lower = user_message.lower()

    # Check if we're waiting for reset confirmation
    if state.get("conversation_stage") == "reset_confirmation":
        # Check confirmation response
        # "сброс" = user wants to reset, so it's a CONFIRM (yes, cancel the order)
        confirm_patterns = [r"\bда\b", r"\bотмени", r"\bподтвержд", r"\bточно\b", r"\bсброс", r"\bудали"]
        cancel_patterns = [r"\bнет\b", r"\bне\s*надо", r"\bпередумал", r"\bоставь", r"\bпродолж"]

        if any(re.search(p, user_message_lower) for p in confirm_patterns):
            return handle_order_reset(state, confirmed=True)
        elif any(re.search(p, user_message_lower) for p in cancel_patterns):
            state["conversation_stage"] = "confirming"
            from app.agents.tools.order_tools import format_order_summary
            summary = format_order_summary(state.get("order_draft", {}))
            state["messages"].append({
                "role": "assistant",
                "content": f"Хорошо, продолжаем с текущим заказом.\n\n{summary}\n\n✅ Пожалуйста, подтвердите заказ.",
                "timestamp": state["updated_at"]
            })
            state["next_step"] = "end"
            return state
        else:
            # Unclear response, ask again
            state["messages"].append({
                "role": "assistant",
                "content": "Пожалуйста, уточните: Вы хотите отменить заказ? (Да/Нет)",
                "timestamp": state["updated_at"]
            })
            state["next_step"] = "end"
            return state

    # FAST PATH: Very obvious reset commands (single word or very clear)
    # This is optimization only - LLM will catch more nuanced cases
    obvious_reset = ["сброс", "сброс заказа", "отмена заказа", "удалить заказ"]
    if user_message_lower.strip() in obvious_reset:
        return handle_order_reset(state, confirmed=False)

    # Classify intent using LLM (handles nuanced cases)
    intent_result = classify_intent(user_message, state["messages"])
    intent = intent_result["intent"]

    # Update state with classified intent
    state["last_intent"] = intent

    # PRIORITY: Handle order_reset intent FIRST (before any stage checks)
    # This ensures reset works from ANY stage (ordering, confirming, etc.)
    if intent == "order_reset":
        return handle_order_reset(state, confirmed=False)

    # Handle POST_ORDER stage (user has a recently confirmed order)
    # Route based on intent - only show order if they want to modify it or check status
    if state.get("conversation_stage") == "post_order":
        from datetime import datetime, timedelta, timezone
        from app.database.database import SessionLocal
        from app.database.models import AIGeneratedOrder

        # Helper function to get validated order and time since confirmation
        def get_order_with_time():
            db = SessionLocal()
            try:
                conversation_id = state.get("conversation_id")
                validated_order = db.query(AIGeneratedOrder).filter(
                    AIGeneratedOrder.conversation_id == conversation_id,
                    AIGeneratedOrder.validation_status == 'validated'
                ).order_by(AIGeneratedOrder.confirmed_at.desc()).first()

                time_since = None
                if validated_order and validated_order.confirmed_at:
                    confirmed_at = validated_order.confirmed_at
                    if confirmed_at.tzinfo is None:
                        confirmed_at = confirmed_at.replace(tzinfo=timezone.utc)
                    time_since = datetime.now(timezone.utc) - confirmed_at

                return validated_order, time_since, db
            except:
                db.close()
                return None, None, None

        # Handle order_status - show confirmed order details
        if intent == "order_status":
            validated_order, time_since, db = get_order_with_time()
            try:
                if validated_order:
                    from app.agents.tools.order_tools import format_order_summary
                    summary = format_order_summary(state.get("order_draft", {}))

                    edit_note = ""
                    if time_since and time_since <= timedelta(hours=ORDER_EDIT_WINDOW_HOURS):
                        minutes_left = ORDER_EDIT_WINDOW_HOURS * 60 - int(time_since.total_seconds() / 60)
                        edit_note = f"\n\n💡 Можно изменить ещё {minutes_left} мин. Напишите «изменить заказ» если нужно."

                    state["messages"].append({
                        "role": "assistant",
                        "content": f"📋 Ваш заказ #{validated_order.id}:\n\n{summary}{edit_note}",
                        "timestamp": state["updated_at"]
                    })
                else:
                    state["messages"].append({
                        "role": "assistant",
                        "content": "У Вас нет активных заказов. Хотите оформить новый?",
                        "timestamp": state["updated_at"]
                    })
                state["next_step"] = "end"
                return state
            finally:
                if db:
                    db.close()

        if intent == "order_modification":
            # User wants to modify their order - check if within edit window
            validated_order, time_since, db = get_order_with_time()
            try:
                if validated_order and time_since:
                    if time_since <= timedelta(hours=ORDER_EDIT_WINDOW_HOURS):
                        # Within edit window - allow modification
                        validated_order.validation_status = 'pending'  # Revert to pending for editing
                        db.commit()

                        from app.agents.tools.order_tools import format_order_summary
                        summary = format_order_summary(state.get("order_draft", {}))
                        minutes_left = ORDER_EDIT_WINDOW_HOURS * 60 - int(time_since.total_seconds() / 60)
                        state["messages"].append({
                            "role": "assistant",
                            "content": f"Ваш подтверждённый заказ (можно изменить ещё {minutes_left} мин):\n\n{summary}\n\nЧто Вы хотели бы изменить?",
                            "timestamp": state["updated_at"]
                        })
                        state["conversation_stage"] = "confirming"
                        state["next_step"] = "end"
                        return state
                    else:
                        # Edit window expired
                        state["messages"].append({
                            "role": "assistant",
                            "content": f"К сожалению, время редактирования заказа истекло ({ORDER_EDIT_WINDOW_HOURS} ч после подтверждения). Для изменений, пожалуйста, свяжитесь с менеджером.\n\nМогу помочь Вам с новым заказом?",
                            "timestamp": state["updated_at"]
                        })
                        state["conversation_stage"] = "inquiry"
                        state["next_step"] = "end"
                        return state
            finally:
                if db:
                    db.close()

        # For greeting in post_order stage - mention the recent order subtly
        if intent == "greeting":
            validated_order, time_since, db = get_order_with_time()
            try:
                edit_note = ""
                if validated_order and time_since and time_since <= timedelta(hours=ORDER_EDIT_WINDOW_HOURS):
                    minutes_left = ORDER_EDIT_WINDOW_HOURS * 60 - int(time_since.total_seconds() / 60)
                    edit_note = f"\n\n💡 Кстати, Ваш недавний заказ #{validated_order.id} ещё можно изменить ({minutes_left} мин). Напишите «изменить заказ», если нужно."

                state["messages"].append({
                    "role": "assistant",
                    "content": f"Здравствуйте! 👋 Чем могу Вам помочь?{edit_note}",
                    "timestamp": state["updated_at"]
                })
                state["conversation_stage"] = "inquiry"
                # Clear order_draft for fresh start (keep validated order in DB)
                state["order_draft"] = {
                    "items": [],
                    "completeness": {"items": False, "pickup": False, "customer": False, "payment": False}
                }
                state["next_step"] = "end"
                return state
            finally:
                if db:
                    db.close()

        # For any other intent in post_order stage - respond normally
        # Clear the post_order stage and order_draft for fresh start
        state["conversation_stage"] = "inquiry"
        state["order_draft"] = {
            "items": [],
            "completeness": {"items": False, "pickup": False, "customer": False, "payment": False}
        }
        # Continue to normal intent routing below

    # Handle order_modification intent (for non-post_order stages)
    if intent == "order_modification":
        order_draft = state.get("order_draft", {})
        if order_draft.get("items"):
            # Has active order - go to confirmation node which handles modifications
            state["conversation_stage"] = "confirming"
            state["next_step"] = "confirm"
            return state
        else:
            # No order yet, treat as order placement
            state["next_step"] = "order_collector"
            return state

    # Smart greeting handling
    if intent == "greeting":
        # Check conversation context
        order_draft = state.get("order_draft", {})
        has_active_order = bool(order_draft.get("items"))
        stage = state.get("conversation_stage", "inquiry")

        # If in confirming stage with active order, redirect back to confirmation
        if stage == "confirming" and has_active_order:
            from app.agents.tools.order_tools import format_order_summary
            summary = format_order_summary(order_draft)
            response_text = f"""Здравствуйте! 👋

У Вас есть незавершённый заказ:

{summary}

Подтверждаете? Напишите «Да» или «Заново», если хотите начать сначала."""
            state["messages"].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": state["updated_at"]
            })
            state["next_step"] = "end"
            return state
        # Full greeting if: inquiry stage (reset/start) OR no active order
        elif stage == "inquiry" or not has_active_order:
            state["next_step"] = "greet"
            return state
        else:
            # Mid-conversation greeting - brief acknowledgment
            state["next_step"] = "acknowledgment"
            return state
    
    # Check if in confirming stage OR if this is an edit request after completion
    stage = state.get("conversation_stage")
    if stage == "confirming":
        state["next_step"] = "confirm"
        return state

    # Handle post-completion edits (conversation was reopened)
    # Check for edit-related keywords
    edit_keywords = [r"\bизмен", r"\bпоменя", r"\bредактир", r"\bисправ"]
    if any(re.search(keyword, user_message.lower()) for keyword in edit_keywords):
        # Check if we have an existing order to edit
        order_draft = state.get("order_draft", {})
        if order_draft.get("items"):
            # Show current order and ask what to change
            from app.agents.tools.order_tools import format_order_summary
            summary = format_order_summary(order_draft)
            response_text = f"""Ваш текущий заказ:

{summary}

Что именно Вы хотели бы изменить? Пожалуйста, укажите новые детали."""

            state["messages"].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": state["updated_at"]
            })
            state["conversation_stage"] = "ordering"
            state["next_step"] = "end"
            return state
    
    # Check for escalation conditions
    should_esc, reason = should_escalate(state, intent, user_message)
    if should_esc:
        state["escalation_reason"] = reason
        state["flagged_for_human"] = True
        state["next_step"] = "escalate"
        return state

    # Route based on intent
    intent_routing = {
        "greeting": "greet",
        "product_inquiry": "product_inquiry",
        "order_placement": "order_collector",
        "order_info_provision": "order_collector",
        "acknowledgment": "acknowledgment",
        "customization_request": "escalate",  # Always escalate
        "delivery_inquiry": "info_provider",
        "payment_inquiry": "info_provider",
        "order_status": "escalate",  # Requires DB lookup, escalate for now
        "complaint": "escalate",  # Always escalate
        "small_talk": "small_talk"
    }
    
    next_node = intent_routing.get(intent, "product_inquiry")  # Default to product inquiry
    state["next_step"] = next_node
    
    return state


def should_continue(state: ConversationState) -> str:
    """
    Conditional edge - Determines next node based on state
    """
    next_step = state.get("next_step", "end")
    
    if state.get("flagged_for_human"):
        return "escalate"
    
    if next_step == "end":
        return END
    
    return next_step


# Build the graph
workflow = StateGraph(ConversationState)

# Add nodes
workflow.add_node("router", router_node)
workflow.add_node("greet", greeting_node)
workflow.add_node("product_inquiry", product_inquiry_node)
workflow.add_node("order_collector", order_collector_node)
workflow.add_node("confirm", confirmation_node)
workflow.add_node("acknowledgment", acknowledgment_node)
workflow.add_node("escalate", escalation_node)
workflow.add_node("info_provider", info_provider_node)
workflow.add_node("small_talk", small_talk_node)

# Set entry point
workflow.set_entry_point("router")

# All specialized nodes END after execution (no loop back to router)
workflow.add_edge("greet", END)
workflow.add_edge("product_inquiry", END)
workflow.add_edge("order_collector", END)
workflow.add_edge("confirm", END)
workflow.add_edge("acknowledgment", END)
workflow.add_edge("info_provider", END)
workflow.add_edge("small_talk", END)
workflow.add_edge("escalate", END)

# Add conditional edges from router
workflow.add_conditional_edges(
    "router",
    should_continue,
    {
        "greet": "greet",
        "product_inquiry": "product_inquiry",
        "order_collector": "order_collector",
        "confirm": "confirm",
        "acknowledgment": "acknowledgment",
        "escalate": "escalate",
        "info_provider": "info_provider",
        "small_talk": "small_talk",
        END: END
    }
)

# Compile graph
order_graph = workflow.compile()
