import pytest
from pydantic import ValidationError
from app.schemas import ProductIn, SupplierIn

def test_product_rejects_selling_price_below_cost():
    with pytest.raises(ValidationError):
        ProductIn(name="Widget", sku="W-1", category_id=1, cost_price="20", selling_price="10", reorder_level=1, reorder_quantity=2)

def test_supplier_phone_must_be_ten_digits():
    with pytest.raises(ValidationError):
        SupplierIn(supplier_code="SUP1", name="Example", email="vendor@example.com", phone="123", lead_time_days=2)
