"""
Product Tools - Database queries and utilities for product catalog
"""
from sqlalchemy.orm import Session
from app.database.models import Product
from typing import Optional


def get_all_products(db: Session, category: Optional[str] = None) -> list[Product]:
    """Get all available products, optionally filtered by category"""
    query = db.query(Product).filter(Product.available == True)
    if category:
        query = query.filter(Product.category == category)
    return query.all()


def get_product_by_id(db: Session, product_id: str) -> Optional[Product]:
    """Get product by product_id"""
    return db.query(Product).filter(
        Product.product_id == product_id,
        Product.available == True
    ).first()


def search_products(db: Session, query: str) -> list[Product]:
    """Search products by name or description"""
    search_term = f"%{query}%"
    return db.query(Product).filter(
        Product.available == True,
        (Product.name.ilike(search_term) | Product.description.ilike(search_term))
    ).all()


def format_product_catalog(products: list[Product]) -> str:
    """Format product list for LLM context"""
    lines = []
    for p in products:
        if p.price_per_kg:
            # Format price without decimals if it's a whole number
            price = int(p.price_per_kg) if p.price_per_kg == int(p.price_per_kg) else p.price_per_kg
            price_str = f"{price}₸/кг"
        elif p.fixed_price:
            price = int(p.fixed_price) if p.fixed_price == int(p.fixed_price) else p.fixed_price
            price_str = f"{price}₸"
        else:
            price_str = "цена не указана"

        lines.append(f"• {p.name} ({p.product_id}): {price_str}")
        if p.description:
            lines.append(f"  {p.description}")

    return "\n".join(lines)


def calculate_price(product: Product, quantity: float) -> float:
    """Calculate price for given quantity (kg for cakes, sets for fixed-price items)"""
    if product.fixed_price:
        # Fixed price items - quantity is number of sets
        return float(product.fixed_price) * quantity
    elif product.price_per_kg:
        # Per-kg items - quantity is weight in kg
        return float(product.price_per_kg) * quantity
    return 0.0


# Emoji map for product flavors
_FLAVOR_EMOJI = {
    "классический": "🍰", "classic": "🍰",
    "шоколадный": "🍫", "chocolate": "🍫", "шоколадт": "🍫",
    "клубничный": "🍓", "strawberry": "🍓", "клубникал": "🍓",
    "кофейный": "☕", "coffee": "☕", "кофе": "☕",
    "карамельный": "🍬", "caramel": "🍬", "карамел": "🍬",
    "малиновый": "🫐", "raspberry": "🫐", "малин": "🫐",
    "фисташковый": "🥜", "pistachio": "🥜", "фисташ": "🥜",
    "ванильный": "🍦", "vanilla": "🍦", "ваниль": "🍦",
    "ассорти": "🎨", "mix": "🎨",
}


def _get_emoji(name: str) -> str:
    """Get emoji for a product based on its name"""
    name_lower = name.lower()
    for key, emoji in _FLAVOR_EMOJI.items():
        if key in name_lower:
            return emoji
    return "🍰"


def _format_price(value) -> str:
    """Format price without decimals if whole number"""
    if value is None:
        return "—"
    price = int(value) if value == int(value) else value
    return f"{price}₸"


def format_menu_for_user(products: list[Product], lang: str = "ru") -> str:
    """
    Format product menu for display to the user in a strict, consistent style.
    This is THE ONLY function that should be used to show the menu to the user.
    
    Args:
        products: list of Product objects from DB
        lang: 'ru' or 'kz'
    
    Returns:
        Formatted menu string
    """
    cakes = [p for p in products if p.category == "cake"]
    sets = [p for p in products if p.category == "dessert_set"]
    
    if lang == "kz":
        lines = ["🍰 *Біздің мәзір:*", ""]
        
        if cakes:
            lines.append("*Торттар (кг бойынша):*")
            for p in cakes:
                emoji = _get_emoji(p.name)
                price = _format_price(p.price_per_kg)
                lines.append(f"  {emoji} {p.name} — {price}/кг")
            lines.append("")
        
        if sets:
            lines.append("*Жиынтықтар (6 дана):*")
            for p in sets:
                emoji = _get_emoji(p.name)
                price = _format_price(p.fixed_price)
                lines.append(f"  {emoji} {p.name} — {price}")
            lines.append("")
        
        lines.append("📏 Ең аз салмақ — 1.5 кг")
        lines.append("⏰ Дайындау уақыты — кемінде 4 сағат")
        lines.append("")
        lines.append("Қай торт Сізді қызықтырады? 😊")
    else:
        lines = ["🍰 *Наше меню:*", ""]
        
        if cakes:
            lines.append("*Торты (по кг):*")
            for p in cakes:
                emoji = _get_emoji(p.name)
                price = _format_price(p.price_per_kg)
                lines.append(f"  {emoji} {p.name} — {price}/кг")
            lines.append("")
        
        if sets:
            lines.append("*Наборы (6 шт):*")
            for p in sets:
                emoji = _get_emoji(p.name)
                price = _format_price(p.fixed_price)
                lines.append(f"  {emoji} {p.name} — {price}")
            lines.append("")
        
        lines.append("📏 Минимальный вес — 1.5 кг")
        lines.append("⏰ Время подготовки — от 4 часов")
        lines.append("")
        lines.append("Какой торт Вас интересует? 😊")
    
    return "\n".join(lines)
