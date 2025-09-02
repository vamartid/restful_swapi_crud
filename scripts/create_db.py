import sys
import pymysql
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

def create_database(host, port, root_user, root_password, db_name, db_user, db_password):
    connection = None
    try:
        connection = pymysql.connect(host=host, user=root_user, password=root_password, port=port)
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
            logging.info(f"Database '{db_name}' created or already exists.")

            cursor.execute(f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_password}';")
            logging.info(f"User '{db_user}' created or already exists.")

            cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'%';")
            cursor.execute("FLUSH PRIVILEGES;")
            logging.info(f"Privileges granted to user '{db_user}' on database '{db_name}'.")
        connection.commit()
    except Exception as e:
        handle_db_exception(e, context=f"Error creating database: {e}")
        sys.exit(1)
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    import os
    from scripts.load_db_config import get_db_config
    logging.info(f"Running script: {os.path.abspath(__file__)}")
    cfg = get_db_config(require_root=True, expected_keys=[
        "host", "port", "root_user", "root_password", "db_name", "db_user", "db_password"
    ])
    create_database(**cfg)