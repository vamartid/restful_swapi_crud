import logging
import os
from colorama import init as colorama_init
from logging.handlers import RotatingFileHandler

# initialize colorama for Windows
colorama_init(autoreset=True)

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[37m",   # gray
        logging.INFO: "\033[36m",    # cyan
        logging.WARNING: "\033[33m", # yellow
        logging.ERROR: "\033[31m",   # red
        logging.CRITICAL: "\033[41m" # red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

def setup_logging(
    log_to_terminal=True,
    log_to_file=True,
    level=logging.INFO,
    log_dir="logs"
):
    """
    Central logging configuration.

    Args:
        log_to_terminal (bool): enable colored logs in terminal
        log_to_file (bool): enable saving logs to files
        level (int): logging level
        log_dir (str): directory for log files
    """
    os.makedirs(log_dir, exist_ok=True)
    
    # ------------------ App root logger ------------------
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    if log_to_terminal:
        terminal_handler = logging.StreamHandler()
        terminal_handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))
        root.addHandler(terminal_handler)

    if log_to_file:
        app_file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=5_000_000,
            backupCount=5
        )
        app_file_handler.setFormatter(formatter)
        root.addHandler(app_file_handler)

    # ------------------ Uvicorn logging ------------------
    if log_to_file:
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_logger.setLevel(level)
        uvicorn_file_handler = RotatingFileHandler(
            os.path.join(log_dir, "uvicorn.log"),
            maxBytes=5_000_000,
            backupCount=5
        )
        uvicorn_file_handler.setFormatter(formatter)
        # Avoid duplicating handlers
        if not any(isinstance(h, RotatingFileHandler) and "uvicorn.log" in h.baseFilename 
                   for h in uvicorn_logger.handlers):
            uvicorn_logger.addHandler(uvicorn_file_handler)

        # Optional: disable Uvicorn's default console logs if desired
        # uvicorn_logger.propagate = False
