from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    """Import models so they register on Base.metadata (used by Alembic)."""
    import app.models  # noqa: F401
