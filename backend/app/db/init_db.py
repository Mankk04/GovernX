"""
Creates all tables. Run once at startup / via `python -m app.db.init_db`.
"""
from app.core.database import Base, engine
from app.models import models  # noqa: F401  (ensures models are registered)


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("GovernX database tables created.")
