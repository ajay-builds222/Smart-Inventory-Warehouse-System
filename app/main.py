from fastapi import FastAPI
from app.routers import auth, catalog, operations, orders

app = FastAPI(
    title="Smart Inventory & Warehouse Management System",
    version="0.1.0",
    description="Modular starter backend. Review README for implemented scope and remaining work.",
)
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(operations.router)
app.include_router(orders.router)

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}
