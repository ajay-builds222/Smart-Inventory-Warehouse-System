from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem, Supplier, Customer, Product, Warehouse, Inventory, StockMovement, User
from app.auth.dependencies import require_roles, get_current_user
from app.utils.email import send_email

router = APIRouter(tags=["Orders"])
MANAGERS=("Admin","Inventory Manager")

class POItemIn(BaseModel):
    product_id: int
    quantity_ordered: int = Field(gt=0)
    unit_cost: Decimal = Field(gt=0)
class POIn(BaseModel):
    po_number: str
    supplier_id: int
    warehouse_id: int
    expected_delivery_date: datetime | None = None
    items: list[POItemIn] = Field(min_length=1)
class ReceiveIn(BaseModel):
    items: list[dict]
class SOItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
class SOIn(BaseModel):
    so_number: str
    customer_id: int
    warehouse_id: int
    items: list[SOItemIn] = Field(min_length=1)
class DispatchIn(BaseModel):
    courier_name: str = Field(min_length=1)
    tracking_number: str = Field(min_length=1)

@router.post("/purchase-orders", status_code=201)
def create_po(data: POIn, db: Session=Depends(get_db), user: User=Depends(require_roles(*MANAGERS))):
    supplier=db.get(Supplier,data.supplier_id); wh=db.get(Warehouse,data.warehouse_id)
    if not supplier or not supplier.is_active: raise HTTPException(400,"Supplier not found or inactive")
    if not wh or not wh.is_active: raise HTTPException(400,"Warehouse not found or inactive")
    if db.scalar(select(PurchaseOrder).where(PurchaseOrder.po_number==data.po_number)): raise HTTPException(409,"PO number already exists")
    expected=data.expected_delivery_date or datetime.utcnow()+timedelta(days=supplier.lead_time_days)
    po=PurchaseOrder(po_number=data.po_number,supplier_id=supplier.id,warehouse_id=wh.id,expected_delivery_date=expected,status="Draft",created_by=user.id)
    po.items=[PurchaseOrderItem(product_id=x.product_id,quantity_ordered=x.quantity_ordered,unit_cost=x.unit_cost,quantity_received=0) for x in data.items]
    po.total_amount=sum((x.unit_cost*x.quantity_ordered for x in data.items),Decimal("0"))
    db.add(po); db.commit(); db.refresh(po); return po

@router.put("/purchase-orders/{po_id}/approve")
def approve_po(po_id: int, db: Session=Depends(get_db), user: User=Depends(require_roles(*MANAGERS))):
    po=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==po_id).with_for_update())
    if not po: raise HTTPException(404,"Purchase order not found")
    if po.status!="Draft": raise HTTPException(409,"Only Draft orders can be approved")
    po.status="Approved"; db.commit()
    return {"id":po.id,"status":po.status,"note":"Email notification can be queued after SMTP configuration."}

@router.put("/purchase-orders/{po_id}/cancel")
def cancel_po(po_id: int, db: Session=Depends(get_db), user: User=Depends(require_roles(*MANAGERS))):
    po=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==po_id).with_for_update())
    if not po: raise HTTPException(404,"Purchase order not found")
    if po.status not in ("Draft","Approved") or any(i.quantity_received for i in po.items): raise HTTPException(409,"This purchase order cannot be cancelled")
    po.status="Cancelled"; db.commit(); return {"id":po.id,"status":po.status}

@router.post("/purchase-orders/{po_id}/receive")
def receive_po(po_id: int, data: ReceiveIn, db: Session=Depends(get_db), user: User=Depends(get_current_user)):
    if user.role not in ("Admin","Inventory Manager","Warehouse Staff"): raise HTTPException(403,"Insufficient permissions")
    try:
        po=db.scalar(select(PurchaseOrder).where(PurchaseOrder.id==po_id).with_for_update())
        if not po: raise HTTPException(404,"Purchase order not found")
        if po.status not in ("Approved","Partially Received"): raise HTTPException(409,"Only approved POs can receive stock")
        if user.role=="Warehouse Staff" and user.warehouse_id!=po.warehouse_id: raise HTTPException(403,"Warehouse access denied")
        wh=db.scalar(select(Warehouse).where(Warehouse.id==po.warehouse_id).with_for_update())
        for entry in data.items:
            item=next((i for i in po.items if i.id==entry.get("item_id")),None)
            qty=entry.get("quantity")
            if not item or not isinstance(qty,int) or qty<=0: raise HTTPException(422,"Each item requires a valid item_id and positive quantity")
            if item.quantity_received+qty>item.quantity_ordered: raise HTTPException(409,"Received quantity exceeds ordered quantity")
            inv=db.scalar(select(Inventory).where(Inventory.product_id==item.product_id,Inventory.warehouse_id==po.warehouse_id).with_for_update())
            if not inv:
                inv=Inventory(product_id=item.product_id,warehouse_id=po.warehouse_id,quantity_on_hand=0,quantity_reserved=0,created_by=user.id); db.add(inv); db.flush()
            current_total=db.scalar(select(Inventory.quantity_on_hand).where(Inventory.warehouse_id==po.warehouse_id))
            total=db.scalar(select(__import__("sqlalchemy").func.coalesce(__import__("sqlalchemy").func.sum(Inventory.quantity_on_hand),0)).where(Inventory.warehouse_id==po.warehouse_id)) or 0
            if total+qty>wh.capacity: raise HTTPException(409,"Warehouse capacity exceeded")
            inv.quantity_on_hand+=qty; item.quantity_received+=qty
            db.add(StockMovement(product_id=item.product_id,warehouse_id=po.warehouse_id,movement_type="Purchase Receipt",quantity=qty,reference_id=po.id,balance_after=inv.quantity_on_hand,performed_by=user.id))
        po.status="Received" if all(i.quantity_received==i.quantity_ordered for i in po.items) else "Partially Received"
        if po.status=="Received": po.received_at=datetime.utcnow()
        db.commit()
        return {"id":po.id,"status":po.status,"received_at":po.received_at}
    except Exception:
        db.rollback()
        raise

@router.post("/sales-orders", status_code=201)
def create_so(data: SOIn, db: Session=Depends(get_db), user: User=Depends(require_roles(*MANAGERS))):
    customer=db.get(Customer,data.customer_id); wh=db.get(Warehouse,data.warehouse_id)
    if not customer or not customer.is_active: raise HTTPException(400,"Customer not found or inactive")
    if not wh or not wh.is_active: raise HTTPException(400,"Warehouse not found or inactive")
    if db.scalar(select(SalesOrder).where(SalesOrder.so_number==data.so_number)): raise HTTPException(409,"SO number already exists")
    so=SalesOrder(so_number=data.so_number,customer_id=customer.id,warehouse_id=wh.id,status="Draft",created_by=user.id)
    subtotal=Decimal("0")
    for line in data.items:
        product=db.get(Product,line.product_id)
        if not product or not product.is_active: raise HTTPException(400,f"Product {line.product_id} not found or inactive")
        total=product.selling_price*line.quantity; subtotal+=total
        so.items.append(SalesOrderItem(product_id=product.id,quantity=line.quantity,unit_price=product.selling_price,line_total=total))
    so.subtotal=subtotal; so.tax_amount=(subtotal*Decimal("0.18")).quantize(Decimal("0.01")); so.grand_total=so.subtotal+so.tax_amount
    db.add(so); db.commit(); db.refresh(so); return so

@router.put("/sales-orders/{so_id}/confirm")
def confirm_so(so_id: int, db: Session=Depends(get_db), user: User=Depends(require_roles(*MANAGERS))):
    try:
        so=db.scalar(select(SalesOrder).where(SalesOrder.id==so_id).with_for_update())
        if not so: raise HTTPException(404,"Sales order not found")
        if so.status!="Draft": raise HTTPException(409,"Only Draft orders can be confirmed")
        customer=db.scalar(select(Customer).where(Customer.id==so.customer_id).with_for_update())
        open_total=sum((x.grand_total for x in db.scalars(select(SalesOrder).where(SalesOrder.customer_id==customer.id,SalesOrder.status.in_(["Confirmed","Picked","Packed","Dispatched"])))),Decimal("0"))
        if open_total+so.grand_total>customer.credit_limit: raise HTTPException(409,"Customer credit limit exceeded")
        locked=[]
        for line in so.items:
            inv=db.scalar(select(Inventory).where(Inventory.product_id==line.product_id,Inventory.warehouse_id==so.warehouse_id).with_for_update())
            if not inv or inv.quantity_available<line.quantity: raise HTTPException(409,f"Insufficient available stock for product {line.product_id}")
            locked.append((inv,line))
        for inv,line in locked: inv.quantity_reserved+=line.quantity
        so.status="Confirmed"; db.commit()
        return {"id":so.id,"status":so.status}
    except Exception:
        db.rollback()
        raise

@router.put("/sales-orders/{so_id}/cancel")
def cancel_so(so_id: int, db: Session=Depends(get_db), user: User=Depends(require_roles(*MANAGERS))):
    try:
        so=db.scalar(select(SalesOrder).where(SalesOrder.id==so_id).with_for_update())
        if not so: raise HTTPException(404,"Sales order not found")
        if so.status not in ("Draft","Confirmed"): raise HTTPException(409,"Only Draft or Confirmed orders can be cancelled")
        if so.status=="Confirmed":
            for line in so.items:
                inv=db.scalar(select(Inventory).where(Inventory.product_id==line.product_id,Inventory.warehouse_id==so.warehouse_id).with_for_update())
                if inv: inv.quantity_reserved-=line.quantity
        so.status="Cancelled"; db.commit(); return {"id":so.id,"status":so.status}
    except Exception:
        db.rollback(); raise

def _warehouse_order(so_id, db, user):
    so=db.scalar(select(SalesOrder).where(SalesOrder.id==so_id).with_for_update())
    if not so: raise HTTPException(404,"Sales order not found")
    if user.role=="Warehouse Staff" and user.warehouse_id!=so.warehouse_id: raise HTTPException(403,"Warehouse access denied")
    if user.role not in ("Admin","Warehouse Staff"): raise HTTPException(403,"Insufficient permissions")
    return so

@router.put("/sales-orders/{so_id}/pick")
def pick_so(so_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    so=_warehouse_order(so_id,db,user)
    if so.status!="Confirmed": raise HTTPException(409,"Order must be Confirmed to pick")
    so.status="Picked"; db.commit(); return {"id":so.id,"status":so.status}

@router.put("/sales-orders/{so_id}/pack")
def pack_so(so_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    so=_warehouse_order(so_id,db,user)
    if so.status!="Picked": raise HTTPException(409,"Order must be Picked to pack")
    so.status="Packed"; db.commit(); return {"id":so.id,"status":so.status}

@router.put("/sales-orders/{so_id}/dispatch")
def dispatch_so(so_id:int, data:DispatchIn, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    try:
        so=_warehouse_order(so_id,db,user)
        if so.status!="Packed": raise HTTPException(409,"Order must be Packed before dispatch")
        if db.scalar(select(SalesOrder).where(SalesOrder.tracking_number==data.tracking_number)): raise HTTPException(409,"Tracking number already exists")
        for line in so.items:
            inv=db.scalar(select(Inventory).where(Inventory.product_id==line.product_id,Inventory.warehouse_id==so.warehouse_id).with_for_update())
            if not inv or inv.quantity_on_hand<line.quantity or inv.quantity_reserved<line.quantity: raise HTTPException(409,"Reserved stock inconsistency")
            inv.quantity_on_hand-=line.quantity; inv.quantity_reserved-=line.quantity
            db.add(StockMovement(product_id=line.product_id,warehouse_id=so.warehouse_id,movement_type="Sale Dispatch",quantity=-line.quantity,reference_id=so.id,balance_after=inv.quantity_on_hand,performed_by=user.id))
        so.status="Dispatched"; so.courier_name=data.courier_name; so.tracking_number=data.tracking_number; so.dispatched_at=datetime.utcnow()
        db.commit(); return {"id":so.id,"status":so.status,"tracking_number":so.tracking_number}
    except Exception:
        db.rollback(); raise

@router.put("/sales-orders/{so_id}/deliver")
def deliver_so(so_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_user)):
    so=_warehouse_order(so_id,db,user)
    if so.status!="Dispatched": raise HTTPException(409,"Order must be Dispatched to deliver")
    so.status="Delivered"; so.delivered_at=datetime.utcnow(); db.commit(); return {"id":so.id,"status":so.status}
