"""Initial schema for smart inventory.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create tables in dependency order. This migration is an initial schema snapshot.
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table("categories",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text()), sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_table("suppliers",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("supplier_code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(10), nullable=False), sa.Column("gst_number", sa.String(15)),
        sa.Column("address", sa.Text()), sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_table("warehouses",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("warehouse_code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("city", sa.String(100), nullable=False),
        sa.Column("address", sa.Text(), nullable=False), sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("manager_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_foreign_key("fk_users_warehouse", "users", "warehouses", ["warehouse_id"], ["id"])
    op.create_table("products",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(180), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False, unique=True), sa.Column("barcode", sa.String(80), unique=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False), sa.Column("cost_price", sa.Numeric(12,2), nullable=False),
        sa.Column("selling_price", sa.Numeric(12,2), nullable=False), sa.Column("reorder_level", sa.Integer(), nullable=False),
        sa.Column("reorder_quantity", sa.Integer(), nullable=False), sa.Column("preferred_supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id")),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_table("customers",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("customer_code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False), sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(10), nullable=False), sa.Column("address", sa.Text()),
        sa.Column("credit_limit", sa.Numeric(12,2), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_table("inventory",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False), sa.Column("quantity_reserved", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
    )
    op.create_table("purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("po_number", sa.String(40), nullable=False, unique=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("expected_delivery_date", sa.DateTime()), sa.Column("received_at", sa.DateTime()),
        sa.Column("total_amount", sa.Numeric(14,2), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_table("purchase_order_items",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity_ordered", sa.Integer(), nullable=False), sa.Column("quantity_received", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12,2), nullable=False),
    )
    op.create_table("sales_orders",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("so_number", sa.String(40), nullable=False, unique=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("subtotal", sa.Numeric(14,2), nullable=False), sa.Column("tax_amount", sa.Numeric(14,2), nullable=False),
        sa.Column("grand_total", sa.Numeric(14,2), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("courier_name", sa.String(120)), sa.Column("tracking_number", sa.String(120), unique=True),
        sa.Column("dispatched_at", sa.DateTime()), sa.Column("delivered_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_table("sales_order_items",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sales_order_id", sa.Integer(), sa.ForeignKey("sales_orders.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("unit_price", sa.Numeric(12,2), nullable=False),
        sa.Column("line_total", sa.Numeric(14,2), nullable=False),
    )
    op.create_table("stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), sa.ForeignKey("warehouses.id"), nullable=False),
        sa.Column("movement_type", sa.String(40), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reference_id", sa.Integer()), sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("performed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table("returns",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sales_order_id", sa.Integer(), sa.ForeignKey("sales_orders.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("refund_amount", sa.Numeric(14,2), nullable=False), sa.Column("rejection_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id")),
    )
    op.create_table("return_items",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("return_id", sa.Integer(), sa.ForeignKey("returns.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("condition", sa.String(20)),
    )
    op.create_table("audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(60), nullable=False), sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.Integer()), sa.Column("old_value", sa.Text()), sa.Column("new_value", sa.Text()),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

def downgrade():
    for table in ["audit_logs","return_items","returns","stock_movements","sales_order_items","sales_orders","purchase_order_items","purchase_orders","inventory","customers","products","warehouses","suppliers","categories","users"]:
        op.drop_table(table)
