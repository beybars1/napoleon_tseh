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
