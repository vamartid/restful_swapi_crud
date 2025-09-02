# tests/test_db_exceptions.py
import pytest
from unittest.mock import patch
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError, NoSuchModuleError
from app.db_exceptions import handle_db_exception

# -------------------- Tests --------------------

def test_operational_error_logs():
    e = OperationalError("statement", {}, "orig")
    with patch("logging.error") as mock_log, patch("sys.exit") as mock_exit:
        handle_db_exception(e, context="testing op error")
        mock_log.assert_any_call(
            "Could not connect during testing op error. Check if the database exists and credentials are correct."
        )
        mock_exit.assert_called_once_with(1)


def test_programming_error_table_not_found():
    e = ProgrammingError("statement", {}, "Table 'foo' doesn't exist")
    with patch("logging.error") as mock_log, patch("sys.exit") as mock_exit:
        # Should NOT exit
        handle_db_exception(e, context="testing prog error")
        mock_log.assert_any_call(
            "testing prog error: table not found. It looks like the database tables have not been created yet. Please run `python scripts/create_tables.py`."
        )
        mock_exit.assert_not_called()


def test_programming_error_permission_denied():
    e = ProgrammingError("statement", {}, "permission denied")
    with patch("logging.error") as mock_log, patch("sys.exit") as mock_exit:
        handle_db_exception(e, context="testing perm error")
        mock_log.assert_any_call(
            "Permission error during testing perm error. Database user may lack required privileges."
        )
        mock_exit.assert_called_once_with(1)


def test_integrity_error():
    e = IntegrityError("stmt", {}, "orig")
    with patch("logging.error") as mock_log, patch("sys.exit") as mock_exit:
        handle_db_exception(e, context="testing integrity")
        mock_log.assert_any_call(
            "Integrity error during testing integrity. Possible duplicate keys or constraint violation."
        )
        mock_exit.assert_called_once_with(1)


def test_no_such_module_error():
    e = NoSuchModuleError("pymysql")
    with patch("logging.error") as mock_log, patch("sys.exit") as mock_exit:
        handle_db_exception(e, context="testing nosuchmodule")
        mock_log.assert_any_call(
            "Database driver not found during testing nosuchmodule. Ensure the required driver (e.g., `pymysql`) is installed."
        )
        mock_exit.assert_called_once_with(1)

def test_unknown_error_re_raises():
    class CustomError(Exception):
        pass

    e = CustomError("oops")
    with patch("logging.error") as mock_log:
        # Call handler with exit_on_error=False
        with pytest.raises(CustomError):
            handle_db_exception(e, context="testing custom", exit_on_error=False)

        mock_log.assert_any_call("Unknown error during testing custom.")
