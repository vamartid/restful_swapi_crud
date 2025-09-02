from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
SessionLocal = None
engine = None

def init_db(db_user, db_password, db_host, db_name, db_port=3306, driver="mysql+pymysql"):
    import logging
    global engine, SessionLocal
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if driver.startswith("sqlite"):
        DATABASE_URL = f"sqlite:///{db_name}"  # db_name can be ":memory:"
    else:
        DATABASE_URL = f"{driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    engine = create_engine(DATABASE_URL, echo=False, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def get_db():
    """
    Dependency for FastAPI routes.
    Yields a database session and ensures it's closed after use.
    """
    if SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized. Call init_db() first.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
