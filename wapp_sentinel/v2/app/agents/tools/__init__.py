"""
AI Agent Tools - Functions for product queries, order management, and escalation
"""

from .product_tools import (
    get_all_products,
    get_product_by_id,
    search_products,
    format_product_catalog,
    calculate_price
)

from .order_tools import (
    validate_pickup_date,
    validate_phone,
    check_order_completeness,
    format_order_summary
)

from .escalation_tools import (
    should_escalate,
    format_escalation_summary,
    increment_clarification
)

__all__ = [
    "get_all_products",
    "get_product_by_id",
    "search_products",
    "format_product_catalog",
    "calculate_price",
    "validate_pickup_date",
    "validate_phone",
    "check_order_completeness",
    "format_order_summary",
    "should_escalate",
    "format_escalation_summary",
    "increment_clarification"
]
__all__ = [
    # Product tools
    "get_products",
    "get_product_details",
    "validate_item",
    # Order tools
    "add_to_cart",
    "calculate_total",
    "check_timing",
    # Escalation tools
    "should_escalate_to_human",
]
