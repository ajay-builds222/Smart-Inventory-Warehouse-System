from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Role = Literal["Admin", "Inventory Manager", "Warehouse Staff"]
Unit = Literal["Piece", "Box", "Kg", "Litre"]

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    role: Role = "Warehouse Staff"
    warehouse_id: int | None = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    warehouse_id: int | None
    is_active: bool

class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None

class CategoryOut(ORMModel):
    id: int
    name: str
    description: str | None
    is_active: bool

class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    sku: str = Field(min_length=1, max_length=80)
    barcode: str | None = None
    category_id: int
    unit: Unit = "Piece"
    cost_price: Decimal = Field(gt=0)
    selling_price: Decimal = Field(gt=0)
    reorder_level: int = Field(ge=0)
    reorder_quantity: int = Field(ge=0)
    preferred_supplier_id: int | None = None
    @model_validator(mode="after")
    def price_check(self):
        if self.selling_price < self.cost_price:
            raise ValueError("selling_price must be greater than or equal to cost_price")
        return self

class ProductOut(ORMModel):
    id: int
    name: str
    sku: str
    barcode: str | None
    category_id: int
    unit: str
    cost_price: Decimal
    selling_price: Decimal
    reorder_level: int
    reorder_quantity: int
    preferred_supplier_id: int | None
    is_active: bool

class WarehouseIn(BaseModel):
    warehouse_code: str = Field(min_length=1, max_length=40)
    name: str
    city: str
    address: str
    capacity: int = Field(gt=0)
    manager_id: int | None = None

class WarehouseOut(ORMModel):
    id: int
    warehouse_code: str
    name: str
    city: str
    address: str
    capacity: int
    manager_id: int | None
    is_active: bool

class SupplierIn(BaseModel):
    supplier_code: str
    name: str
    email: EmailStr
    phone: str = Field(pattern=r"^\d{10}$")
    gst_number: str | None = Field(default=None, pattern=r"^[0-9A-Z]{15}$")
    address: str | None = None
    lead_time_days: int = Field(default=0, ge=0)

class SupplierOut(ORMModel):
    id: int
    supplier_code: str
    name: str
    email: EmailStr
    phone: str
    gst_number: str | None
    address: str | None
    lead_time_days: int
    is_active: bool

class CustomerIn(BaseModel):
    customer_code: str
    name: str
    email: EmailStr
    phone: str = Field(pattern=r"^\d{10}$")
    address: str | None = None
    credit_limit: Decimal = Field(ge=0)

class CustomerOut(ORMModel):
    id: int
    customer_code: str
    name: str
    email: EmailStr
    phone: str
    address: str | None
    credit_limit: Decimal
    is_active: bool
