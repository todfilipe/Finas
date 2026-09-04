from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import DATABASE_URL, DB_CONNECT_SECONDS


def opcoes_de_ligacao():
    if (DATABASE_URL or "").startswith("postgresql"):
        return {"connect_timeout": DB_CONNECT_SECONDS}

    return {}


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=opcoes_de_ligacao(),
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
