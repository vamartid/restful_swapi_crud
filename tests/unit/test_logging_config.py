# tests/test_logging_config.py

import logging
from pathlib import Path
import pytest
from app.logging_config import setup_logging, ColorFormatter

def test_color_formatter_wraps_message():
    fmt = ColorFormatter("%(levelname)s: %(message)s")
    record = logging.LogRecord(
        name="test", level=logging.ERROR, pathname="", lineno=0,
        msg="Test message", args=(), exc_info=None
    )
    result = fmt.format(record)
    # Check ANSI codes and message content
    assert result.startswith("\033[31m")  # red for ERROR
    assert result.endswith("\033[0m")
    assert "Test message" in result

def test_log_dir_creation(tmp_path):
    log_dir = tmp_path / "logs"
    setup_logging(log_to_terminal=False, log_to_file=True, log_dir=log_dir)
    # Ensure directory is created
    assert log_dir.exists()
    # Ensure file handler is added
    root = logging.getLogger()
    assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers)

def test_terminal_handler_added(tmp_path):
    setup_logging(log_to_terminal=True, log_to_file=False, log_dir=tmp_path)
    root = logging.getLogger()
    assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)
    # No file handler
    assert all(not isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers)

def test_file_and_terminal_handlers(tmp_path):
    setup_logging(log_to_terminal=True, log_to_file=True, log_dir=tmp_path)
    root = logging.getLogger()
    handler_types = [type(h) for h in root.handlers]
    assert logging.StreamHandler in handler_types
    assert logging.handlers.RotatingFileHandler in handler_types

@pytest.mark.parametrize("level,ansi", [
    (logging.DEBUG, "\033[37m"),
    (logging.INFO, "\033[36m"),
    (logging.WARNING, "\033[33m"),
    (logging.ERROR, "\033[31m"),
    (logging.CRITICAL, "\033[41m"),
])
def test_all_log_levels(level, ansi):
    fmt = ColorFormatter("%(levelname)s: %(message)s")
    record = logging.LogRecord(
        name="test", level=level, pathname="", lineno=0,
        msg="Level test", args=(), exc_info=None
    )
    result = fmt.format(record)
    assert result.startswith(ansi)
    assert result.endswith("\033[0m")
    assert "Level test" in result
