import os
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.auth.security import hash_password

def main():
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD in your terminal first.")
    if len(password) < 12:
        raise SystemExit("Use an admin password with at least 12 characters.")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("A user with this email already exists.")
        db.add(User(email=email, full_name="System Administrator", password_hash=hash_password(password), role="Admin", is_active=True))
        db.commit()
    print("Admin user created.")

if __name__ == "__main__":
    main()
