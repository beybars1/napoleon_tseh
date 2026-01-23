"""
Order Tools - Validation and management for order drafts
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re
import os

# Business rules
MIN_CAKE_WEIGHT_KG = 1.5  # Minimum weight for cakes
MAX_ORDER_ITEMS = 5  # Maximum number of different products per order

# Timezone configuration
ALMATY_UTC_OFFSET = 6  # Almaty is UTC+6


def validate_pickup_date(date_str: str, time_str: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate pickup date meets 4-hour minimum lead time
    
    Args:
        date_str: Date in format DD.MM.YYYY
        time_str: Optional time in format HH:MM
    
    Returns:
        (is_valid, error_message)
    """
    try:
        # Parse various date formats
        for fmt in ["%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"]:
            try:
                pickup_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        else:
            return False, "Не могу распознать дату. Используйте формат ДД.ММ.ГГГГ"
        
        # Add time if provided
        if time_str:
            try:
                time_obj = datetime.strptime(time_str, "%H:%M")
                pickup_date = pickup_date.replace(hour=time_obj.hour, minute=time_obj.minute)
            except ValueError:
                pass  # If time parse fails, use date only
        
        # Check 4-hour minimum
        # Get current time in Almaty timezone (UTC+6)
        now = datetime.now()
        # If container is in UTC, adjust to Almaty time
        # Otherwise assume container already in correct timezone
        if os.getenv('TZ') != 'Asia/Almaty':
            # Assume UTC, add 6 hours for Almaty
            now = now + timedelta(hours=ALMATY_UTC_OFFSET)
        
        min_datetime = now + timedelta(hours=4)
        
        if pickup_date < min_datetime:
            return False, f"Минимальное время подготовки — 4 часа. Самая ранняя дата/время: {min_datetime.strftime('%d.%m.%Y %H:%M')}"
        
        return True, None
        
    except Exception as e:
        return False, f"Ошибка проверки даты: {str(e)}"
        return False, f"Ошибка проверки даты: {str(e)}"


def validate_phone(phone: str) -> tuple[bool, Optional[str]]:
    """
    Validate Kazakhstan phone number
    
    Returns:
        (is_valid, cleaned_phone or error_message)
    """
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    # Check Kazakhstan patterns: +7, 8, or 77
    if digits.startswith('7') and len(digits) == 11:
        return True, f"+{digits}"
    elif digits.startswith('8') and len(digits) == 11:
        return True, f"+7{digits[1:]}"
    elif len(digits) == 10:
        return True, f"+7{digits}"
    else:
        return False, "Укажите корректный номер телефона (например: +77001234567)"


def check_order_completeness(order_draft: dict) -> dict[str, bool]:
    """
    Check which order sections are complete
    
    Returns:
        {"items": bool, "pickup": bool, "customer": bool, "payment": bool}
    """
    return {
        "items": bool(order_draft.get("items") and len(order_draft["items"]) > 0),
        "pickup": bool(order_draft.get("pickup_date") and order_draft.get("pickup_time")),
        "customer": bool(order_draft.get("customer_name") and order_draft.get("customer_phone")),
        "payment": bool(order_draft.get("payment_method"))
    }


def validate_product_availability(db, product_id: int) -> Tuple[bool, Optional[str]]:
    """
    Check if product is available for order
    
    Returns:
        (is_available, error_message)
    """
    from app.database.models import Product
    
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        return False, "Продукт не найден в каталоге"
    
    if not product.available:
        return False, f"К сожалению, {product.name} временно недоступен. Выберите другой торт."
    
    return True, None


def validate_item_weight(weight_kg: float, product_category: str) -> Tuple[bool, Optional[str]]:
    """
    Validate item weight based on business rules
    
    Returns:
        (is_valid, error_message)
    """
    if product_category == "cake":
        if weight_kg < MIN_CAKE_WEIGHT_KG:
            return False, f"Минимальный вес торта — {MIN_CAKE_WEIGHT_KG} кг"
        if weight_kg > 10:
            return False, "Максимальный вес торта — 10 кг. Для больших заказов свяжитесь с менеджером."
    
    return True, None


def validate_order_size(items: list) -> Tuple[bool, Optional[str]]:
    """
    Validate order doesn't exceed maximum items
    
    Returns:
        (is_valid, error_message)
    """
    if len(items) > MAX_ORDER_ITEMS:
        return False, f"Максимум {MAX_ORDER_ITEMS} позиций в одном заказе. Для больших заказов свяжитесь с менеджером."
    
    return True, None


def format_price(price: float) -> str:
    """Format price without decimals if it's a whole number"""
    if price == int(price):
        return f"{int(price)}₸"
    return f"{price:.0f}₸"


def format_order_summary(order_draft: dict) -> str:
    """Format order draft for confirmation"""
    lines = ["📋 Ваш заказ:"]

    if order_draft.get("items"):
        lines.append("\n🍰 Продукты:")
        for item in order_draft["items"]:
            qty = item.get("quantity", 0)
            total_price = item.get("price", 0)
            is_fixed_price = item.get("is_fixed_price", False)

            if is_fixed_price:
                # Fixed-price item (sets)
                unit_price = item.get("unit_price", total_price)
                if qty == 1:
                    lines.append(f"  • {item.get('name', 'N/A')} — {format_price(total_price)}")
                else:
                    lines.append(f"  • {item.get('name', 'N/A')} × {int(qty)} = {format_price(total_price)}")
            else:
                # Per-kg item (cakes)
                price_per_kg = total_price / qty if qty > 0 else 0
                lines.append(f"  • {item.get('name', 'N/A')} — {qty} кг × {format_price(price_per_kg)}/кг = {format_price(total_price)}")

    if order_draft.get("pickup_date"):
        lines.append(f"\n📅 Дата получения: {order_draft['pickup_date']}")
    if order_draft.get("pickup_time"):
        lines.append(f"🕐 Время: {order_draft['pickup_time']}")

    if order_draft.get("customer_name"):
        lines.append(f"\n👤 Имя: {order_draft['customer_name']}")
    if order_draft.get("customer_phone"):
        lines.append(f"📞 Телефон: {order_draft['customer_phone']}")

    if order_draft.get("payment_method"):
        lines.append(f"\n💳 Оплата: {order_draft['payment_method']}")

    # Calculate total from items (each item.price is already total)
    total = sum(item.get("price", 0) for item in order_draft.get("items", []))
    if total > 0:
        lines.append(f"\n💰 ИТОГО: {format_price(total)}")

    return "\n".join(lines)
