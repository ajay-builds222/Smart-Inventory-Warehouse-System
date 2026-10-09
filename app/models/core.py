from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Warehouse Staff", nullable=False)
    warehouse_id: Mapped[int | None] = mapped_column(ForeignKey("warehouses.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    products: Mapped[list["Product"]] = relationship(back_populates="category")

class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(10))
    gst_number: Mapped[str | None] = mapped_column(String(15))
    address: Mapped[str | None] = mapped_column(Text)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="supplier")

class Warehouse(Base, TimestampMixin):
    __tablename__ = "warehouses"
    id: Mapped[int] = mapped_column(primary_key=True)
    warehouse_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(Text)
    capacity: Mapped[int] = mapped_column(Integer)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="warehouse")

class Product(Base, TimestampMixin):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(80), unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    unit: Mapped[str] = mapped_column(String(20), default="Piece")
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    reorder_quantity: Mapped[int] = mapped_column(Integer, default=0)
    preferred_supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped[Category] = relationship(back_populates="products")
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    preferred_supplier: Mapped[Supplier | None] = relationship(foreign_keys=[preferred_supplier_id])

class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"
    __table_args__ = (UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0)
    product: Mapped[Product] = relationship(back_populates="inventory")
    warehouse: Mapped[Warehouse] = relationship(back_populates="inventory")
    @property
    def quantity_available(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(10))
    address: Mapped[str | None] = mapped_column(Text)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    expected_delivery_date: Mapped[datetime | None] = mapped_column(DateTime)
    received_at: Mapped[datetime | None] = mapped_column(DateTime)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="Draft")
    supplier: Mapped[Supplier] = relationship(back_populates="purchase_orders")
    items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="purchase_order", cascade="all, delete-orphan")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity_ordered: Mapped[int] = mapped_column(Integer)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

class SalesOrder(Base, TimestampMixin):
    __tablename__ = "sales_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    so_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="Draft")
    courier_name: Mapped[str | None] = mapped_column(String(120))
    tracking_number: Mapped[str | None] = mapped_column(String(120), unique=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    customer: Mapped[Customer] = relationship()
    items: Mapped[list["SalesOrderItem"]] = relationship(back_populates="sales_order", cascade="all, delete-orphan")

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    sales_order: Mapped[SalesOrder] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    movement_type: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[int] = mapped_column(Integer)
    reference_id: Mapped[int | None] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

class ReturnRequest(Base, TimestampMixin):
    __tablename__ = "returns"
    id: Mapped[int] = mapped_column(primary_key=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id"))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Requested")
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    items: Mapped[list["ReturnItem"]] = relationship(back_populates="return_request", cascade="all, delete-orphan")

class ReturnItem(Base):
    __tablename__ = "return_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    return_id: Mapped[int] = mapped_column(ForeignKey("returns.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    condition: Mapped[str | None] = mapped_column(String(20))
    return_request: Mapped[ReturnRequest] = relationship(back_populates="items")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
