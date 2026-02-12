"""
Order Tools - Validation and management for order drafts
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re
import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Business rules
MIN_CAKE_WEIGHT_KG = 1.5  # Minimum weight for cakes
MAX_ORDER_ITEMS = 5  # Maximum number of different products per order

# Timezone configuration
ALMATY_UTC_OFFSET = 6  # Almaty is UTC+6

# OpenAI client for smart date parsing
_openai_client = None

def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def get_almaty_now() -> datetime:
    """Get current datetime in Almaty timezone (UTC+6)"""
    now = datetime.now()
    if os.getenv('TZ') != 'Asia/Almaty':
        now = now + timedelta(hours=ALMATY_UTC_OFFSET)
    return now


def resolve_natural_date(date_text: str, time_text: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Use LLM to resolve natural language date/time expressions into structured DD.MM.YYYY and HH:MM.
    
    Handles expressions like:
    - "завтра", "послезавтра", "ертең", "бүрсігүні"
    - "следующий понедельник", "келесі дүйсенбі"
    - "следующая суббота", "келесі сенбі"
    - "через 2 дня", "2 күннен кейін"
    - "на следующей неделе в этот же день"
    - "25 января", "25 қаңтар"
    - Standard formats: "25.01.2026", "25.01"
    - Vague times: "на вечер", "утром", "после обеда", "кешке", "таңертең"
    
    Returns:
        (date_str in DD.MM.YYYY format or None, time_str in HH:MM format or None)
    """
    now = get_almaty_now()
    
    # Resolve vague time expressions BEFORE anything else
    if time_text:
        vague_time_map = {
            "утро": "10:00", "утром": "10:00", "таңертең": "10:00", "таңғы": "10:00",
            "день": "14:00", "днём": "14:00", "днем": "14:00", "обед": "13:00",
            "после обеда": "15:00", "түстен кейін": "15:00",
            "вечер": "18:00", "вечером": "18:00", "на вечер": "18:00", "кешке": "18:00", "кешкі": "18:00",
        }
        normalized_time = time_text.strip().lower()
        if normalized_time in vague_time_map:
            time_text = vague_time_map[normalized_time]
            logger.info(f"[DATE_RESOLVER] Vague time '{normalized_time}' → {time_text}")
    
    # First try simple regex for standard date formats (avoid LLM call)
    combined = f"{date_text} {time_text}" if time_text else date_text
    
    # Standard format DD.MM.YYYY or DD.MM.YY
    simple_match = re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$', date_text.strip())
    if simple_match:
        day, month, year = simple_match.groups()
        if len(year) == 2:
            year = "20" + year
        resolved_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
        resolved_time = None
        if time_text:
            time_match = re.match(r'^(\d{1,2})[:\.\s](\d{2})$', time_text.strip())
            if time_match:
                resolved_time = f"{time_match.group(1).zfill(2)}:{time_match.group(2)}"
        return resolved_date, resolved_time
    
    # DD.MM without year
    simple_match2 = re.match(r'^(\d{1,2})\.(\d{1,2})\.?$', date_text.strip())
    if simple_match2:
        day, month = simple_match2.groups()
        resolved_date = f"{day.zfill(2)}.{month.zfill(2)}.{now.year}"
        resolved_time = None
        if time_text:
            time_match = re.match(r'^(\d{1,2})[:\.\s](\d{2})$', time_text.strip())
            if time_match:
                resolved_time = f"{time_match.group(1).zfill(2)}:{time_match.group(2)}"
        return resolved_date, resolved_time

    # For anything else (natural language), use LLM
    try:
        client = _get_openai_client()
        
        # Build a concrete calendar reference for LLM (eliminates arithmetic errors)
        weekday_names_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        today_weekday = now.weekday()  # 0=Mon, 6=Sun
        today_name = weekday_names_ru[today_weekday]
        
        # Generate calendar: remaining days this week + all of next week
        calendar_lines = []
        # Days from today through end of next week (up to 14 days)
        for offset in range(0, 15):
            d = now + timedelta(days=offset)
            wd = d.weekday()
            name = weekday_names_ru[wd]
            label = ""
            if offset == 0:
                label = " ← СЕГОДНЯ"
            elif offset == 1:
                label = " ← завтра"
            # Mark which week
            # Current week: days until next Sunday
            days_to_sunday = 6 - today_weekday  # days until this Sunday
            if offset <= days_to_sunday:
                week_label = "(эта неделя)"
            else:
                week_label = "(СЛЕДУЮЩАЯ неделя)"
            calendar_lines.append(f"  {d.strftime('%d.%m.%Y')} — {name} {week_label}{label}")
        
        calendar_str = "\n".join(calendar_lines)
        
        prompt = f"""Определи точную дату и время из текста клиента.

СЕГОДНЯ: {now.strftime('%d.%m.%Y')} ({today_name}), время: {now.strftime('%H:%M')}

КАЛЕНДАРЬ (используй его для выбора правильной даты):
{calendar_str}

ТЕКСТ ДАТЫ: "{date_text}"
ТЕКСТ ВРЕМЕНИ: "{time_text if time_text else 'не указано'}"

ПРАВИЛА ОПРЕДЕЛЕНИЯ ДАТЫ:
- "завтра" / "ертең" → следующий день (см. календарь)
- "послезавтра" / "бүрсігүні" → через 2 дня (см. календарь)
- "следующий/следующая [день недели]" / "келесі [күн]" → этот день на СЛЕДУЮЩЕЙ неделе (найди в календаре строку с нужным днём и пометкой "СЛЕДУЮЩАЯ неделя")
- "эта суббота" / "в субботу" / "осы сенбі" → суббота ТЕКУЩЕЙ недели (найди в календаре с пометкой "эта неделя")
- "через N дней" / "N күннен кейін" → СЕГОДНЯ + N дней (посчитай по календарю)
- "на следующей неделе" / "келесі аптада" → +7 дней от сегодня
- "25 января" / "25 қаңтар" → 25.01 текущего или следующего года
- ВАЖНО: Выбирай дату ТОЛЬКО из календаря выше! Проверь, что день недели в ответе совпадает!

ПРАВИЛА ВРЕМЕНИ:
- "утром" / "таңертең" → "10:00"
- "днём" / "после обеда" / "түстен кейін" → "15:00"
- "вечером" / "на вечер" / "вечер" / "кешке" → "18:00"
- "15:00", "20 00" → точное время
- Если время НЕ указано → time = null

Отвечай ТОЛЬКО валидным JSON:
{{"date": "DD.MM.YYYY", "time": "HH:MM или null"}}

Если дату невозможно определить:
{{"date": null, "time": null}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты определяешь точную дату и время из текста. Отвечай только валидным JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        resolved_date = result.get("date")
        resolved_time = result.get("time")
        
        # Validate: if user mentioned a specific weekday, verify the resolved date matches
        if resolved_date:
            weekday_map = {
                'понедельник': 0, 'дүйсенбі': 0, 'дуйсенби': 0,
                'вторник': 1, 'сейсенбі': 1, 'сейсенби': 1,
                'среда': 2, 'среду': 2, 'сәрсенбі': 2, 'сарсенби': 2,
                'четверг': 3, 'бейсенбі': 3, 'бейсенби': 3,
                'пятница': 4, 'пятницу': 4, 'жұма': 4, 'жума': 4,
                'суббота': 5, 'субботу': 5, 'сенбі': 5, 'сенби': 5,
                'воскресенье': 6, 'жексенбі': 6, 'жексенби': 6,
            }
            text_lower = date_text.lower()
            expected_weekday = None
            for word, wd in weekday_map.items():
                if word in text_lower:
                    expected_weekday = wd
                    break
            
            if expected_weekday is not None:
                try:
                    parsed = datetime.strptime(resolved_date, "%d.%m.%Y")
                    actual_weekday = parsed.weekday()
                    if actual_weekday != expected_weekday:
                        logger.warning(f"[DATE_RESOLVER] Weekday mismatch! Text='{date_text}', expected weekday={expected_weekday}, got={actual_weekday} ({resolved_date}). Correcting...")
                        # Find the correct date: search in the next 14 days
                        is_next_week = any(w in text_lower for w in ['следующ', 'келесі', 'келеси'])
                        for offset in range(1 if is_next_week else 0, 15):
                            candidate = now + timedelta(days=offset)
                            if candidate.weekday() == expected_weekday:
                                if is_next_week and offset <= (6 - today_weekday):
                                    continue  # Skip this week for "следующий"
                                resolved_date = candidate.strftime("%d.%m.%Y")
                                logger.info(f"[DATE_RESOLVER] Corrected to {resolved_date}")
                                break
                except ValueError:
                    pass
        
        logger.info(f"[DATE_RESOLVER] '{date_text}' + '{time_text}' → date={resolved_date}, time={resolved_time}")
        return resolved_date, resolved_time
        
    except Exception as e:
        logger.error(f"[DATE_RESOLVER] Error resolving date '{date_text}': {e}")
        return None, None


def validate_pickup_date(date_str: str, time_str: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate pickup date meets 4-hour minimum lead time.
    Supports both structured dates (DD.MM.YYYY) and natural language (завтра, ертең, etc.)
    
    Args:
        date_str: Date in format DD.MM.YYYY or natural language
        time_str: Optional time in format HH:MM or natural language
    
    Returns:
        (is_valid, error_message)
    """
    try:
        # Resolve natural language dates via LLM if needed
        resolved_date, resolved_time = resolve_natural_date(date_str, time_str)
        
        if not resolved_date:
            return False, "Не удалось распознать дату. Укажите, пожалуйста, в формате ДД.ММ.ГГГГ или напишите, например, «завтра», «послезавтра», «следующий понедельник»."
        
        # Use resolved time if original wasn't provided or if LLM extracted one
        if resolved_time and not time_str:
            time_str = resolved_time
        
        # Parse the resolved date
        pickup_date = None
        for fmt in ["%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"]:
            try:
                pickup_date = datetime.strptime(resolved_date, fmt)
                break
            except ValueError:
                continue
        
        if not pickup_date:
            return False, "Не удалось распознать дату. Используйте формат ДД.ММ.ГГГГ"
        
        # Add time if provided
        effective_time = time_str or resolved_time
        if effective_time:
            try:
                time_obj = datetime.strptime(effective_time, "%H:%M")
                pickup_date = pickup_date.replace(hour=time_obj.hour, minute=time_obj.minute)
            except ValueError:
                pass
        
        # Check 4-hour minimum
        now = get_almaty_now()
        min_datetime = now + timedelta(hours=4)
        
        if pickup_date < min_datetime:
            return False, f"Минимальное время подготовки — 4 часа. Самая ранняя дата/время: {min_datetime.strftime('%d.%m.%Y %H:%M')}"
        
        return True, None
        
    except Exception as e:
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
        time_val = order_draft['pickup_time']
        # Map vague time words to readable format
        vague_display = {
            "вечер": "18:00 (вечером)", "вечером": "18:00 (вечером)", "на вечер": "18:00 (вечером)",
            "кешке": "18:00 (кешке)", "кешкі": "18:00 (кешке)",
            "утро": "10:00 (утром)", "утром": "10:00 (утром)",
            "таңертең": "10:00 (таңертең)", "таңғы": "10:00 (таңғы)",
            "день": "14:00 (днём)", "днём": "14:00 (днём)", "днем": "14:00 (днём)",
            "после обеда": "15:00 (после обеда)", "түстен кейін": "15:00 (түстен кейін)",
            "обед": "13:00 (обед)",
        }
        display_time = vague_display.get(time_val.lower(), time_val)
        lines.append(f"🕐 Время: {display_time}")

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
