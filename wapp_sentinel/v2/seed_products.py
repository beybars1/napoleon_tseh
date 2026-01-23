"""
Seed script for products table
Run this after migration to populate initial product catalog
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.database import SessionLocal
from app.database.models import Product
from datetime import datetime

# Napoleon Tseh Product Catalog
PRODUCTS = [
    {
        "product_id": "napoleon_classic",
        "name": "Торт Наполеон Классический",
        "category": "cake",
        "description": "Наш фирменный торт с нежными коржами и классическим заварным кремом",
        "price_per_kg": 8000,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "молоко", "ваниль"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "napoleon_chocolate",
        "name": "Торт Наполеон Шоколадный",
        "category": "cake",
        "description": "Шоколадные коржи с нежным шоколадным кремом",
        "price_per_kg": 9000,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "какао", "шоколад", "молоко"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "napoleon_strawberry",
        "name": "Торт Наполеон Клубничный",
        "category": "cake",
        "description": "Классические коржи с клубничным кремом и свежей клубникой",
        "price_per_kg": 9500,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "клубника", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "napoleon_coffee",
        "name": "Торт Наполеон Кофейный",
        "category": "cake",
        "description": "Ароматные коржи с кофейным кремом для любителей кофе",
        "price_per_kg": 9000,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "кофе", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко", "кофеин"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "napoleon_caramel",
        "name": "Торт Наполеон Карамельный",
        "category": "cake",
        "description": "Нежные коржи с карамельным кремом и карамельной глазурью",
        "price_per_kg": 9000,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "карамель", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "napoleon_raspberry",
        "name": "Торт Наполеон Малиновый",
        "category": "cake",
        "description": "Воздушные коржи с малиновым кремом и свежей малиной",
        "price_per_kg": 9500,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "малина", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "napoleon_pistachio",
        "name": "Торт Наполеон Фисташковый",
        "category": "cake",
        "description": "Изысканный торт с фисташковым кремом и фисташками",
        "price_per_kg": 10000,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "фисташки", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко", "орехи"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "napoleon_vanilla",
        "name": "Торт Наполеон Ванильный",
        "category": "cake",
        "description": "Классические коржи с насыщенным ванильным кремом",
        "price_per_kg": 8500,
        "fixed_price": None,
        "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
        "ingredients": ["мука", "масло", "яйца", "сахар", "ваниль", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "mini_napoleon_classic_set",
        "name": "Набор мини-Наполеонов Классический",
        "category": "dessert_set",
        "description": "6 порционных пирожных Наполеон классический - идеально для чаепития",
        "price_per_kg": None,
        "fixed_price": 4500,
        "sizes": None,
        "ingredients": ["мука", "масло", "яйца", "сахар", "молоко", "ваниль"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "mini_napoleon_chocolate_set",
        "name": "Набор мини-Наполеонов Шоколадный",
        "category": "dessert_set",
        "description": "6 порционных шоколадных пирожных Наполеон",
        "price_per_kg": None,
        "fixed_price": 5000,
        "sizes": None,
        "ingredients": ["мука", "масло", "яйца", "сахар", "какао", "шоколад", "молоко"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "mini_napoleon_mix_set",
        "name": "Набор мини-Наполеонов Ассорти",
        "category": "dessert_set",
        "description": "6 порционных пирожных: 3 классических + 3 шоколадных",
        "price_per_kg": None,
        "fixed_price": 4800,
        "sizes": None,
        "ingredients": ["мука", "масло", "яйца", "сахар", "молоко", "ваниль", "какао", "шоколад"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "mini_napoleon_strawberry_set",
        "name": "Набор мини-Наполеонов Клубничный",
        "category": "dessert_set",
        "description": "6 порционных клубничных пирожных Наполеон",
        "price_per_kg": None,
        "fixed_price": 5200,
        "sizes": None,
        "ingredients": ["мука", "масло", "яйца", "сахар", "клубника", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко"],
        "preparation_hours": 4,
        "available": True
    },
    {
        "product_id": "mini_napoleon_coffee_set",
        "name": "Набор мини-Наполеонов Кофейный",
        "category": "dessert_set",
        "description": "6 порционных кофейных пирожных Наполеон",
        "price_per_kg": None,
        "fixed_price": 5000,
        "sizes": None,
        "ingredients": ["мука", "масло", "яйца", "сахар", "кофе", "сливки", "молоко"],
        "allergens": ["глютен", "яйца", "молоко", "кофеин"],
        "preparation_hours": 4,
        "available": True
    },
]


def seed_products():
    """Seed products table with initial data"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding products table...")
        
        # Check if products already exist
        existing_count = db.query(Product).count()
        if existing_count > 0:
            print(f"⚠️  Products table already has {existing_count} products")
            response = input("Do you want to clear and reseed? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Seeding cancelled")
                return
            
            # Clear existing products
            db.query(Product).delete()
            db.commit()
            print("🗑️  Cleared existing products")
        
        # Insert new products
        for product_data in PRODUCTS:
            product = Product(**product_data)
            db.add(product)
        
        db.commit()
        print(f"✅ Successfully seeded {len(PRODUCTS)} products!")
        
        # Display summary
        print("\n📊 Product Summary:")
        cakes_count = db.query(Product).filter(Product.category == 'cake').count()
        sets_count = db.query(Product).filter(Product.category == 'dessert_set').count()
        print(f"   • Cakes: {cakes_count}")
        print(f"   • Dessert Sets: {sets_count}")
        print(f"   • Total: {cakes_count + sets_count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding products: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_products()
