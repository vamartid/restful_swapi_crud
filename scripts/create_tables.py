import os
import sys
from sqlalchemy.exc import OperationalError
from scripts.load_db_config import get_db_config

from app.logging_config import logging, setup_logging
from app.db_exceptions import handle_db_exception

# -------------------- Logging --------------------

setup_logging(
    log_to_terminal=True,
    log_to_file=False,
    level=logging.INFO,
    log_dir="logs"
)

# -------------------------------------------------

def create_tables(db_user, db_password, db_host="localhost", db_name="swapi_db", db_port=3306):
    import app.models  # ensure all models are imported so Base.metadata is populated
    from app.database import init_db, Base

    try:
        engine = init_db(db_user, db_password, db_host, db_name, db_port)
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables created successfully!")
    except Exception as e:
        handle_db_exception(e, context="creating tables")


if __name__ == "__main__":
    logging.info(f"Running script: {os.path.abspath(__file__)}")
    cfg = get_db_config(
        require_root=False,
        expected_keys=["db_user", "db_password", "db_host", "db_name", "db_port"]
    )
    create_tables(**cfg)
