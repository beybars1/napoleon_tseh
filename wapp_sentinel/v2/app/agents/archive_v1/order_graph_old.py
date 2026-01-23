"""LangGraph workflow definition for order collection"""
from typing import Literal
from langgraph.graph import StateGraph, END
from app.agents.state import OrderState
from app.agents.nodes import (
    greet_customer,
    collect_items,
    collect_delivery,
    collect_payment,
    collect_contacts,
    validate_order,
    confirm_with_customer,
    save_order
)


def route_after_collection(state: OrderState) -> Literal["validate", END]:
    """
    Route after any collection node based on what's been collected.
    """
    # If needs clarification, end and wait for next message
    if state.get("needs_clarification"):
        return END
    
    # If all collected, validate
    if (state.get("has_items") and 
        state.get("has_delivery_info") and 
        state.get("has_payment_info") and 
        state.get("has_contact_info")):
        return "validate"
    
    # Otherwise end and wait for more info
    return END


def route_after_validate(state: OrderState) -> Literal["confirm", END]:
    """
    After validation, either confirm or end.
    """
    if state.get("order_validated"):
        return "confirm"
    else:
        return END


def route_after_confirm(state: OrderState) -> Literal["save", END]:
    """
    After showing confirmation, check if confirmed.
    """
    if state.get("order_confirmed"):
        return "save"
    return END


def create_order_graph() -> StateGraph:
    """
    Create and configure the LangGraph workflow for order collection.
    
    Simplified flow - each message triggers one pass through appropriate node.
    """
    workflow = StateGraph(OrderState)
    
    # Add nodes
    workflow.add_node("greet", greet_customer)
    workflow.add_node("collect_items", collect_items)
    workflow.add_node("collect_delivery", collect_delivery)
    workflow.add_node("collect_payment", collect_payment)
    workflow.add_node("collect_contacts", collect_contacts)
    workflow.add_node("validate", validate_order)
    workflow.add_node("confirm", confirm_with_customer)
    workflow.add_node("save", save_order)
    
    # Set entry point
    workflow.set_entry_point("greet")
    
    # From greet, always end
    workflow.add_edge("greet", END)
    
    # From collection nodes
    workflow.add_conditional_edges(
        "collect_items",
        route_after_collection,
        {"validate": "validate", END: END}
    )
    
    workflow.add_conditional_edges(
        "collect_delivery",
        route_after_collection,
        {"validate": "validate", END: END}
    )
    
    workflow.add_conditional_edges(
        "collect_payment",
        route_after_collection,
        {"validate": "validate", END: END}
    )
    
    workflow.add_conditional_edges(
        "collect_contacts",
        route_after_collection,
        {"validate": "validate", END: END}
    )
    
    # From validate
    workflow.add_conditional_edges(
        "validate",
        route_after_validate,
        {"confirm": "confirm", END: END}
    )
    
    # From confirm
    workflow.add_conditional_edges(
        "confirm",
        route_after_confirm,
        {"save": "save", END: END}
    )
    
    # From save, end
    workflow.add_edge("save", END)
    
    return workflow


# Compile the graph
order_graph = create_order_graph().compile()
