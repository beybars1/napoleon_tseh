from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional

from app.core.database import get_async_session
from app.models.product import Product, ProductCategory, ProductStatus
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[ProductCategory] = Query(None),
    status: Optional[ProductStatus] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all products with filtering"""
    
    query = select(Product)
    
    if category:
        query = query.where(Product.category == category)
    
    if status:
        query = query.where(Product.status == status)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Product.name.ilike(search_term)) |
            (Product.description.ilike(search_term))
        )
    
    query = query.order_by(Product.display_order, Product.name).offset(skip).limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return [
        {
            "id": product.id,
            "uuid": product.uuid,
            "name": product.name,
            "description": product.description,
            "category": product.category.value,
            "base_price": product.price_display,
            "cost": (product.cost / 100.0) if product.cost else 0,
            "image_url": product.image_url,
            "preparation_time": product.preparation_time,
            "is_available": product.status == ProductStatus.ACTIVE and product.is_available_online,
            "is_customizable": product.is_customizable,
            "ingredients": product.ingredients or [],
            "allergens": product.allergens or [],
            "dietary_info": "",  # We can add this field to the model later
            "customization_options": {
                "sizes": product.sizes or [],
                "flavors": product.flavors or [],
                "decorations": product.decorations or [],
            },
            "created_at": product.created_at.isoformat()
        }
        for product in products
    ]


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific product details"""
    
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product.id,
        "uuid": product.uuid,
        "name": product.name,
        "description": product.description,
        "category": product.category.value,
        "base_price": product.price_display,
        "cost": product.cost / 100.0 if product.cost else 0,
        "ingredients": product.ingredients or [],
        "allergens": product.allergens or [],
        "dietary_info": "",  # We can add this field to the model later
        "customization_options": {
            "sizes": product.sizes or [],
            "flavors": product.flavors or [],
            "decorations": product.decorations or [],
        },
        "preparation_time": product.preparation_time,
        "advance_notice": product.advance_notice,
        "stock_quantity": product.stock_quantity,
        "min_stock_level": product.min_stock_level,
        "image_url": product.image_url,
        "images": product.images,
        "display_order": product.display_order,
        "tags": product.tags,
        "is_available": product.status == ProductStatus.ACTIVE and product.is_available_online,
        "is_customizable": product.is_customizable,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat() if product.updated_at else None
    }


@router.post("/")
async def create_product(
    name: str,
    description: Optional[str] = None,
    category: ProductCategory = ProductCategory.CAKE,
    price: float = 0.0,
    cost: Optional[float] = None,
    ingredients: Optional[List[str]] = None,
    allergens: Optional[List[str]] = None,
    preparation_time: Optional[int] = None,
    advance_notice: Optional[int] = None,
    stock_quantity: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new product"""
    
    product = Product(
        name=name,
        description=description,
        category=category,
        price=int(price * 100),  # Convert to cents
        cost=int(cost * 100) if cost else None,
        ingredients=ingredients,
        allergens=allergens,
        preparation_time=preparation_time,
        advance_notice=advance_notice,
        stock_quantity=stock_quantity,
        status=ProductStatus.ACTIVE
    )
    
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    return {
        "message": "Product created successfully",
        "product": {
            "id": product.id,
            "name": product.name,
            "category": product.category.value,
            "price": product.price_display
        }
    }


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[ProductCategory] = None,
    price: Optional[float] = None,
    cost: Optional[float] = None,
    status: Optional[ProductStatus] = None,
    stock_quantity: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update product information"""
    
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if category is not None:
        product.category = category
    if price is not None:
        product.price = int(price * 100)
    if cost is not None:
        product.cost = int(cost * 100)
    if status is not None:
        product.status = status
    if stock_quantity is not None:
        product.stock_quantity = stock_quantity
    
    await db.commit()
    
    return {"message": "Product updated successfully"}


@router.get("/stats/summary")
async def get_product_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get product statistics summary"""
    
    # Total products
    total_result = await db.execute(select(func.count(Product.id)))
    total_products = total_result.scalar()
    
    # Active products
    active_result = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.ACTIVE)
    )
    active_products = active_result.scalar()
    
    # Out of stock products
    out_of_stock_result = await db.execute(
        select(func.count(Product.id)).where(Product.status == ProductStatus.OUT_OF_STOCK)
    )
    out_of_stock_products = out_of_stock_result.scalar()
    
    # Products by category
    category_result = await db.execute(
        select(Product.category, func.count(Product.id))
        .group_by(Product.category)
    )
    category_counts = dict(category_result.all())
    
    return {
        "total_products": total_products,
        "active_products": active_products,
        "out_of_stock_products": out_of_stock_products,
        "category_breakdown": {
            category.value: category_counts.get(category, 0)
            for category in ProductCategory
        }
    } 