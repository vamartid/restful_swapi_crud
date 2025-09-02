import pymysql
import os
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

def drop_database(host, port, root_user, root_password, db_name):
    import sys
    connection = None
    try:
        connection = pymysql.connect(host=host, user=root_user, password=root_password, port=port)
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`;")
            logging.info(f"Database '{db_name}' dropped successfully (if it existed).")
        connection.commit()
    except Exception as e:
        handle_db_exception(e, context=f"Error dropping database '{db_name}'")
        sys.exit(1)
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    from scripts.load_db_config import get_db_config
    logging.info(f"Running script: {os.path.abspath(__file__)}")
    cfg = get_db_config(require_root=True, expected_keys=[
        "host", "port", "root_user", "root_password", "db_name"
    ])
    drop_database(**cfg)
