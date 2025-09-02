def handle_db_exception(e, context="database operation", exit_on_error=True):
    """
    Handle common SQLAlchemy / DB exceptions with friendly logging.

    Args:
        e (Exception): the exception raised
        context (str): description of what was being attempted
        exit_on_error (bool): whether to sys.exit(1) on error (for CLI scripts)
    """
    import logging
    import sys
    from sqlalchemy.exc import (
        OperationalError,
        ProgrammingError,
        IntegrityError,
        NoSuchModuleError,
        SQLAlchemyError
    )

    re_raise = True  # whether to propagate the exception

    if isinstance(e, OperationalError):
        logging.error(
            f"Could not connect during {context}. "
            "Check if the database exists and credentials are correct."
        )
    elif isinstance(e, ProgrammingError):
        if "doesn't exist" in str(e) or "table not found" in str(e).lower():
            logging.error(
                f"{context}: table not found. "
                "It looks like the database tables have not been created yet. "
                "Please run `python scripts/create_tables.py`."
            )
            re_raise = False  # this specific case should not raise
        else:
            logging.error(
                f"Permission error during {context}. "
                "Database user may lack required privileges."
            )
    elif isinstance(e, IntegrityError):
        logging.error(
            f"Integrity error during {context}. "
            "Possible duplicate keys or constraint violation."
        )
    elif isinstance(e, NoSuchModuleError):
        logging.error(
            f"Database driver not found during {context}. "
            "Ensure the required driver (e.g., `pymysql`) is installed."
        )
    elif isinstance(e, SQLAlchemyError):
        logging.error(f"Unexpected SQLAlchemy error during {context}.")
    else:
        logging.error(f"Unknown error during {context}.")
        # Re-raise unknown exceptions in tests or if exit_on_error=False
        if not exit_on_error:
            raise e

    logging.debug(f"Full error: {e}")

    # Decide whether to exit or re-raise
    if exit_on_error and re_raise:
        sys.exit(1)
    elif re_raise:
        raise  # re-raise non-table-not-found SQLAlchemy errors
