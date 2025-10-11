from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.order import Order, OrderCreate
from app.crud import crud_order

router = APIRouter()

@router.post("/", response_model=Order)
async def create_order(
    order_in: OrderCreate,
    db: Session = Depends(deps.get_db),
):
    return await crud_order.create(db=db, obj_in=order_in)

@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
):
    order = await crud_order.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/", response_model=List[Order])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
):
    return await crud_order.get_multi(db=db, skip=skip, limit=limit)

@router.put("/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(deps.get_db),
):
    order = await crud_order.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await crud_order.update_status(db=db, db_obj=order, status=status)
