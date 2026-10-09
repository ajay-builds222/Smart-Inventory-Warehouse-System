from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Category, Product, Inventory, Warehouse, Supplier, Customer, User
from app.schemas import CategoryIn, CategoryOut, ProductIn, ProductOut, WarehouseIn, WarehouseOut, SupplierIn, SupplierOut, CustomerIn, CustomerOut
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Master Data"])
MANAGERS = ("Admin", "Inventory Manager")

@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    if db.scalar(select(Category).where(Category.name == data.name)):
        raise HTTPException(409, "Category already exists")
    obj = Category(**data.model_dump(), created_by=user.id); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(skip: int = 0, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Category).where(Category.is_active.is_(True)).offset(skip).limit(limit)))

@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, data: CategoryIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    obj = db.get(Category, category_id)
    if not obj: raise HTTPException(404, "Category not found")
    for key, value in data.model_dump().items(): setattr(obj, key, value)
    db.commit(); db.refresh(obj); return obj

@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    obj = db.get(Category, category_id)
    if not obj: raise HTTPException(404, "Category not found")
    if db.scalar(select(func.count(Product.id)).where(Product.category_id == category_id, Product.is_active.is_(True))):
        raise HTTPException(409, "Category has active products")
    obj.is_active = False; db.commit()

@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    if db.scalar(select(Product).where(Product.sku == data.sku)): raise HTTPException(409, "SKU already exists")
    if data.barcode and db.scalar(select(Product).where(Product.barcode == data.barcode)): raise HTTPException(409, "Barcode already exists")
    if not db.get(Category, data.category_id): raise HTTPException(404, "Category not found")
    obj = Product(**data.model_dump(), created_by=user.id); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/products", response_model=list[ProductOut])
def list_products(skip: int = 0, limit: int = Query(50, ge=1, le=200), search: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Product).where(Product.is_active.is_(True))
    if search: q = q.where((Product.name.like(f"%{search}%")) | (Product.sku.like(f"%{search}%")))
    return list(db.scalars(q.offset(skip).limit(limit)))

@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.get(Product, product_id)
    if not obj: raise HTTPException(404, "Product not found")
    stock = db.execute(select(Inventory, Warehouse.name).join(Warehouse).where(Inventory.product_id == product_id)).all()
    rows = [{"warehouse_id": inv.warehouse_id, "warehouse_name": name, "quantity_on_hand": inv.quantity_on_hand, "quantity_reserved": inv.quantity_reserved, "quantity_available": inv.quantity_available} for inv, name in stock]
    result = ProductOut.model_validate(obj).model_dump(mode="json")
    result.update({"stock_by_warehouse": rows, "total_stock": sum(r["quantity_on_hand"] for r in rows)})
    return result

@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    obj = db.get(Product, product_id)
    if not obj: raise HTTPException(404, "Product not found")
    for key, value in data.model_dump().items(): setattr(obj, key, value)
    db.commit(); db.refresh(obj); return obj

@router.delete("/products/{product_id}", status_code=204)
def deactivate_product(product_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    obj = db.get(Product, product_id)
    if not obj: raise HTTPException(404, "Product not found")
    if db.scalar(select(func.coalesce(func.sum(Inventory.quantity_on_hand), 0)).where(Inventory.product_id == product_id)) > 0:
        raise HTTPException(409, "Product with stock cannot be deactivated")
    obj.is_active = False; db.commit()

@router.post("/warehouses", response_model=WarehouseOut, status_code=201)
def create_warehouse(data: WarehouseIn, db: Session = Depends(get_db), user: User = Depends(require_roles("Admin"))):
    if db.scalar(select(Warehouse).where(Warehouse.warehouse_code == data.warehouse_code)): raise HTTPException(409, "Warehouse code already exists")
    obj = Warehouse(**data.model_dump(), created_by=user.id); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/warehouses", response_model=list[WarehouseOut])
def list_warehouses(skip: int = 0, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Warehouse).where(Warehouse.is_active.is_(True)).offset(skip).limit(limit)))

@router.get("/warehouses/{warehouse_id}", response_model=WarehouseOut)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = db.get(Warehouse, warehouse_id)
    if not obj: raise HTTPException(404, "Warehouse not found")
    return obj

@router.put("/warehouses/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(warehouse_id: int, data: WarehouseIn, db: Session = Depends(get_db), user: User = Depends(require_roles("Admin"))):
    obj = db.get(Warehouse, warehouse_id)
    if not obj: raise HTTPException(404, "Warehouse not found")
    for key, value in data.model_dump().items(): setattr(obj, key, value)
    db.commit(); db.refresh(obj); return obj

@router.delete("/warehouses/{warehouse_id}", status_code=204)
def deactivate_warehouse(warehouse_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("Admin"))):
    obj = db.get(Warehouse, warehouse_id)
    if not obj: raise HTTPException(404, "Warehouse not found")
    if db.scalar(select(func.coalesce(func.sum(Inventory.quantity_on_hand), 0)).where(Inventory.warehouse_id == warehouse_id)) > 0:
        raise HTTPException(409, "Warehouse with stock cannot be deactivated")
    obj.is_active = False; db.commit()

@router.get("/warehouses/{warehouse_id}/inventory")
def warehouse_inventory(warehouse_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "Warehouse Staff" and user.warehouse_id != warehouse_id: raise HTTPException(403, "Warehouse access denied")
    if not db.get(Warehouse, warehouse_id): raise HTTPException(404, "Warehouse not found")
    rows = db.scalars(select(Inventory).where(Inventory.warehouse_id == warehouse_id)).all()
    return [{"product_id": x.product_id, "quantity_on_hand": x.quantity_on_hand, "quantity_reserved": x.quantity_reserved, "quantity_available": x.quantity_available} for x in rows]


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
def create_supplier(
    data: SupplierIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
):
    existing_supplier = db.scalar(
        select(Supplier).where(
            (Supplier.supplier_code == data.supplier_code)
            | (Supplier.email == str(data.email))
        )
    )

    if existing_supplier:
        raise HTTPException(
            status_code=409,
            detail="Supplier code or email already exists",
        )

    supplier_data = data.model_dump()
    supplier_data["email"] = str(data.email)

    obj = Supplier(**supplier_data, created_by=user.id)

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj

@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(skip: int = 0, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.scalars(select(Supplier).where(Supplier.is_active.is_(True)).offset(skip).limit(limit)))

@router.get("/suppliers/{supplier_id}", response_model=SupplierOut)
def get_supplier(supplier_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj=db.get(Supplier,supplier_id)
    if not obj: raise HTTPException(404,"Supplier not found")
    return obj

@router.put("/suppliers/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, data: SupplierIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    obj=db.get(Supplier,supplier_id)
    if not obj: raise HTTPException(404,"Supplier not found")
    for key,value in data.model_dump().items(): setattr(obj,key,value)
    db.commit(); db.refresh(obj); return obj

@router.delete("/suppliers/{supplier_id}", status_code=204)
def deactivate_supplier(supplier_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("Admin"))):
    obj=db.get(Supplier,supplier_id)
    if not obj: raise HTTPException(404,"Supplier not found")
    obj.is_active=False; db.commit()


@router.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(
    data: CustomerIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*MANAGERS)),
):
    existing_customer = db.scalar(
        select(Customer).where(
            (Customer.customer_code == data.customer_code)
            | (Customer.email == str(data.email))
        )
    )

    if existing_customer:
        raise HTTPException(
            status_code=409,
            detail="Customer code or email already exists",
        )

    customer_data = data.model_dump()
    customer_data["email"] = str(data.email)

    obj = Customer(**customer_data, created_by=user.id)
    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj

@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj=db.get(Customer,customer_id)
    if not obj: raise HTTPException(404,"Customer not found")
    return obj

@router.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, data: CustomerIn, db: Session = Depends(get_db), user: User = Depends(require_roles(*MANAGERS))):
    obj=db.get(Customer,customer_id)
    if not obj: raise HTTPException(404,"Customer not found")
    for key,value in data.model_dump().items(): setattr(obj,key,value)
    db.commit(); db.refresh(obj); return obj
