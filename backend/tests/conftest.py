import unicodedata

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def _sqlite_unaccent(value):
    """Remove acentos — substitui a extension unaccent do Postgres nos testes."""
    if value is None:
        return None
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    dbapi_conn.create_function("unaccent", 1, _sqlite_unaccent)
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))
        conn.commit()


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
