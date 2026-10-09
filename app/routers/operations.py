
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Inventory,
    Product,
    StockMovement,
    PurchaseOrder,
    SalesOrder,
    AuditLog,
    User,
)
from app.auth.dependencies import get_current_user, require_roles


router = APIRouter(tags=["Inventory & Operations"])

MANAGERS = ("Admin", "Inventory Manager")


# --------------------------------------------------
# GET INVENTORY
# --------------------------------------------------
@router.get("/inventory")
def list_inventory(
    product_id: int | None = None,
    warehouse_id: int | None = None,
    low_stock: bool = False,
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Inventory, Product.reorder_level).join(Product)

    if product_id is not None:
        q = q.where(Inventory.product_id == product_id)

    if warehouse_id is not None:
        if (
            user.role == "Warehouse Staff"
            and user.warehouse_id != warehouse_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Warehouse access denied",
            )

        q = q.where(Inventory.warehouse_id == warehouse_id)

    elif user.role == "Warehouse Staff":
        q = q.where(Inventory.warehouse_id == user.warehouse_id)

    rows = db.execute(
        q.order_by(Inventory.id)
        .offset(skip)
        .limit(limit)
    ).all()

    out = []

    for inv, reorder in rows:
        available = inv.quantity_available

        # When low_stock=true, return only items below reorder level.
        if low_stock and available >= reorder:
            continue

        out.append(
            {
                "product_id": inv.product_id,
                "warehouse_id": inv.warehouse_id,
                "quantity_on_hand": inv.quantity_on_hand,
                "quantity_reserved": inv.quantity_reserved,
                "quantity_available": available,
                "reorder_level": reorder,
            }
        )

    return out


# --------------------------------------------------
# GET INVENTORY FOR A SPECIFIC PRODUCT AND WAREHOUSE
# --------------------------------------------------
@router.get("/inventory/{product_id}/{warehouse_id}")
def get_inventory(
    product_id: int,
    warehouse_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if (
        user.role == "Warehouse Staff"
        and user.warehouse_id != warehouse_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Warehouse access denied",
        )

    obj = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == warehouse_id,
        )
    )

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found",
        )

    return {
        "product_id": obj.product_id,
        "warehouse_id": obj.warehouse_id,
        "quantity_on_hand": obj.quantity_on_hand,
        "quantity_reserved": obj.quantity_reserved,
        "quantity_available": obj.quantity_available,
    }


# --------------------------------------------------
# GET STOCK MOVEMENTS
# --------------------------------------------------
@router.get("/stock-movements")
def list_movements(
    product_id: int | None = None,
    warehouse_id: int | None = None,
    movement_type: str | None = None,
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(StockMovement)

    if product_id is not None:
        q = q.where(StockMovement.product_id == product_id)

    if warehouse_id is not None:
        if (
            user.role == "Warehouse Staff"
            and user.warehouse_id != warehouse_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Warehouse access denied",
            )

        q = q.where(StockMovement.warehouse_id == warehouse_id)

    elif user.role == "Warehouse Staff":
        q = q.where(
            StockMovement.warehouse_id == user.warehouse_id
        )

    if movement_type:
        q = q.where(StockMovement.movement_type == movement_type)

    return list(
        db.scalars(
            q.order_by(StockMovement.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )


# --------------------------------------------------
# GET PURCHASE ORDERS
# --------------------------------------------------
@router.get("/purchase-orders")
def list_purchase_orders(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(PurchaseOrder)

    if status:
        q = q.where(PurchaseOrder.status == status)

    return list(
        db.scalars(
            q.order_by(PurchaseOrder.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )


# --------------------------------------------------
# GET A PURCHASE ORDER BY ID
# --------------------------------------------------
@router.get("/purchase-orders/{po_id}")
def get_purchase_order(
    po_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.get(PurchaseOrder, po_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found",
        )

    return obj


# --------------------------------------------------
# GET SALES ORDERS
# --------------------------------------------------
@router.get("/sales-orders")
def list_sales_orders(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(SalesOrder)

    if status:
        q = q.where(SalesOrder.status == status)

    return list(
        db.scalars(
            q.order_by(SalesOrder.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )


# --------------------------------------------------
# GET A SALES ORDER BY ID
# --------------------------------------------------
@router.get("/sales-orders/{so_id}")
def get_sales_order(
    so_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = db.get(SalesOrder, so_id)

    if not obj:
        raise HTTPException(
            status_code=404,
            detail="Sales order not found",
        )

    return obj


# --------------------------------------------------
# DASHBOARD REPORT
# --------------------------------------------------
@router.get("/reports/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
):
    products = (
        db.scalar(
            select(func.count(Product.id)).where(
                Product.is_active.is_(True)
            )
        )
        or 0
    )

    low_stock = (
        db.scalar(
            select(func.count(Inventory.id))
            .join(Product)
            .where(
                (
                    Inventory.quantity_on_hand
                    - Inventory.quantity_reserved
                )
                < Product.reorder_level
            )
        )
        or 0
    )

    pending_po = (
        db.scalar(
            select(func.count(PurchaseOrder.id)).where(
                PurchaseOrder.status.in_(
                    ["Draft", "Approved", "Partially Received"]
                )
            )
        )
        or 0
    )

    pending_so = (
        db.scalar(
            select(func.count(SalesOrder.id)).where(
                SalesOrder.status.in_(
                    ["Confirmed", "Picked", "Packed", "Dispatched"]
                )
            )
        )
        or 0
    )

    return {
        "total_products": products,
        "low_stock_count": low_stock,
        "pending_purchase_orders": pending_po,
        "pending_sales_orders": pending_so,
        "note": (
            "Complete valuation and today's dispatch metrics "
            "in reporting phase."
        ),
    }


# --------------------------------------------------
# ADMIN AUDIT LOGS
# --------------------------------------------------
@router.get("/audit-logs")
def audit_logs(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Admin")),
):
    return list(
        db.scalars(
            select(AuditLog)
            .order_by(AuditLog.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )