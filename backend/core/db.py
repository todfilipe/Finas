from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
