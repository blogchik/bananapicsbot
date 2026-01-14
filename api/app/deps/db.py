from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def db_session_dep() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
