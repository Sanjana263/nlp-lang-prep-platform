"""Create an admin account (admins can't self-register).

Run from backend/:   python -m scripts.create_admin
"""
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


def main() -> None:
    name = input("Admin full name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Password (min 8 chars): ")
    if len(password) < 8 or len(password.encode()) > 72:
        raise SystemExit("Password must be 8-72 bytes.")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("That email already exists.")
        db.add(User(full_name=name, email=email, password_hash=hash_password(password),
                    target_exam="IELTS", role="admin"))
        db.commit()
    print(f"Admin {email} created.")


if __name__ == "__main__":
    main()
