# tests/unit/test_database.py
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db, SessionLocal, init_db
from unittest.mock import patch

# -------------------- Fixtures --------------------
@pytest.fixture(scope="module")
def sqlite_engine():
    """Initialize in-memory SQLite engine and create tables."""
    engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(sqlite_engine):
    """Provide a session for testing."""
    # Create a sessionmaker bound to the SQLite engine
    local_session = sessionmaker(bind=sqlite_engine)

    def sqlite_get_db():
        db = local_session()
        try:
            yield db
        finally:
            db.close()

    # Get a single session for the test
    db_gen = sqlite_get_db()
    db = next(db_gen)
    yield db
    try:
        next(db_gen)  # cleanup generator
    except StopIteration:
        pass

# -------------------- Tests --------------------
def test_init_db_sqlite_engine(sqlite_engine):
    """Check that engine executes a simple query."""
    with sqlite_engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1

def test_get_db_session_works(session):
    """Check that a session works for simple queries."""
    result = session.execute(text("SELECT 1")).scalar()
    assert result == 1

def test_get_db_without_init(monkeypatch):
    """Ensure get_db raises RuntimeError if SessionLocal not initialized."""
    monkeypatch.setattr("app.database.SessionLocal", None)
    with pytest.raises(RuntimeError, match="SessionLocal is not initialized"):
        next(get_db())

def test_init_db_mysql_branch():
    fake_engine = object()
    with patch("app.database.create_engine", return_value=fake_engine):
        engine = init_db(
            db_user="user",
            db_password="pass",
            db_host="localhost",
            db_name="dbname",
            db_port=3306,
            driver="mysql+pymysql"
        )
    assert engine is fake_engine

def test_init_db_sqlite_branch():
    fake_engine = object()
    with patch("app.database.create_engine", return_value=fake_engine):
        engine = init_db(
            db_user="",
            db_password="",
            db_host="",
            db_name=":memory:",
            driver="sqlite"
        )
    assert engine is fake_engine
